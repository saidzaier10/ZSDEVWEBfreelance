import { computed } from 'vue'

export function useQuoteCalculator(quote, options) {
    const { projectTypes, designOptions, complexityLevels, supplementaryOptions } = options

    const getSelectedProjectType = () => {
        return projectTypes.value.find(t => t.id === quote.value.project_type)
    }

    const getSelectedDesignOption = () => {
        return designOptions.value.find(o => o.id === quote.value.design_option)
    }

    const getSelectedComplexityLevel = () => {
        return complexityLevels.value.find(l => l.id === quote.value.complexity_level)
    }

    const getSelectedSupplementaryOptions = () => {
        // Only include one-time billing options, matching backend calculate_prices() filter
        return supplementaryOptions.value.filter(
            o => quote.value.supplementary_options.includes(o.id) && o.billing_type === 'one_time'
        )
    }

    const breakdown = computed(() => {
        const zero = { subtotal_ht: 0, discount_amount: 0, tva_amount: 0, total_ttc: 0 }

        const projectType = getSelectedProjectType()
        const designOption = getSelectedDesignOption()
        const complexityLevel = getSelectedComplexityLevel()
        const suppOptions = getSelectedSupplementaryOptions()

        if (!projectType || !designOption || !complexityLevel) {
            return zero
        }

        // Base price + design supplement, scaled by complexity multiplier
        let subtotal = (Number(projectType.base_price) + Number(designOption.price_supplement))
            * Number(complexityLevel.price_multiplier)

        // Add one-time supplementary options
        suppOptions.forEach(option => {
            subtotal += Number(option.price)
        })

        // Apply discount (before TVA, matching backend)
        const discountType = quote.value.discount_type
        const discountValue = Number(quote.value.discount_value) || 0
        let discountAmount = 0

        if (discountType === 'percent') {
            discountAmount = subtotal * (discountValue / 100)
        } else if (discountType === 'fixed') {
            discountAmount = discountValue
        }

        // Clamp discount so it never exceeds the subtotal
        discountAmount = Math.min(discountAmount, subtotal)

        const subtotalAfterDiscount = subtotal - discountAmount

        // Apply TVA
        const tvaRate = Number(quote.value.tva_rate ?? 20)
        const tvaAmount = subtotalAfterDiscount * (tvaRate / 100)

        const totalTtc = subtotalAfterDiscount + tvaAmount

        return {
            subtotal_ht: Math.round(subtotal * 100) / 100,
            discount_amount: Math.round(discountAmount * 100) / 100,
            tva_amount: Math.round(tvaAmount * 100) / 100,
            total_ttc: Math.round(totalTtc * 100) / 100,
        }
    })

    // Backward-compatible alias
    const total = computed(() => breakdown.value.total_ttc)

    return {
        getSelectedProjectType,
        getSelectedDesignOption,
        getSelectedComplexityLevel,
        getSelectedSupplementaryOptions,
        breakdown,
        total,
    }
}
