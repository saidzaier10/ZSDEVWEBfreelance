import { useTitle } from '@vueuse/core'

const SITE_NAME = 'Zsdevweb'
const DEFAULT_DESCRIPTION = 'Solutions web innovantes et sur mesure.'

export function useSEO(title, description, image = null, jsonLd = null) {
    const fullTitle = `${title} | ${SITE_NAME}`
    const resolvedDescription = description || DEFAULT_DESCRIPTION

    // Update Title
    const pageTitle = useTitle()
    pageTitle.value = fullTitle

    // Update Meta Description
    updateMeta('description', resolvedDescription)

    // Update OG Tags
    updateMeta('og:title', fullTitle, 'property')
    updateMeta('og:description', resolvedDescription, 'property')
    if (image) {
        updateMeta('og:image', image, 'property')
    }

    // Update Twitter Tags
    updateMeta('twitter:title', fullTitle, 'property')
    updateMeta('twitter:description', resolvedDescription, 'property')
    if (image) {
        updateMeta('twitter:image', image, 'property')
    }

    // Update Canonical URL
    const canonicalUrl = window.location.href
    let link = document.querySelector('link[rel="canonical"]')
    if (!link) {
        link = document.createElement('link')
        link.setAttribute('rel', 'canonical')
        document.head.appendChild(link)
    }
    link.setAttribute('href', canonicalUrl)

    // Inject JSON-LD
    if (jsonLd) {
        let script = document.querySelector('script[type="application/ld+json"]')
        if (!script) {
            script = document.createElement('script')
            script.setAttribute('type', 'application/ld+json')
            document.head.appendChild(script)
        }
        script.textContent = JSON.stringify(jsonLd)
    }
}

function updateMeta(name, content, attribute = 'name') {
    let meta = document.querySelector(`meta[${attribute}="${name}"]`)
    if (!meta) {
        meta = document.createElement('meta')
        meta.setAttribute(attribute, name)
        document.head.appendChild(meta)
    }
    meta.setAttribute('content', content)
}
