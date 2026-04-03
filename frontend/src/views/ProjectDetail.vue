<template>
    <div class="min-h-screen bg-white dark:bg-dark-900 transition-colors duration-200">
        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center min-h-screen">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>

        <!-- Error State -->
        <div v-else-if="error" class="flex flex-col justify-center items-center min-h-screen px-4 text-center">
            <h2 class="text-2xl font-bold text-red-600 mb-4">Une erreur est survenue</h2>
            <p class="text-dark-600 dark:text-dark-300 mb-6">{{ error }}</p>
            <router-link to="/portfolio" class="text-primary-600 hover:text-primary-700 font-semibold">
                Retour au portfolio
            </router-link>
        </div>

        <!-- Content -->
        <div v-else-if="project" class="pb-20">
            <!-- Hero Section -->
            <section class="relative h-[60vh] min-h-[400px]">
                <div class="absolute inset-0">
                    <img v-if="project.image_main || project.image" :src="project.image_main || project.image"
                        :alt="project.title" class="w-full h-full object-cover" />
                    <div class="absolute inset-0 bg-gradient-to-t from-dark-900 via-dark-900/60 to-transparent"></div>
                </div>

                <div class="absolute bottom-0 left-0 right-0 py-20">
                    <div class="container mx-auto px-4">
                        <router-link to="/portfolio"
                            class="inline-flex items-center text-white/80 hover:text-white mb-6 transition-colors">
                            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                    d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                            </svg>
                            Retour aux projets
                        </router-link>

                        <h1 class="text-4xl md:text-6xl font-bold text-white mb-4">{{ project.title }}</h1>
                        <p class="text-xl text-gray-200 max-w-2xl">{{ project.short_description }}</p>

                        <div class="flex flex-wrap gap-3 mt-6">
                            <span v-for="tech in project.technologies" :key="tech.id || tech.name"
                                class="px-3 py-1 bg-white/20 backdrop-blur-md border border-white/30 text-white rounded-full text-sm">
                                {{ tech.name || tech }}
                            </span>
                        </div>
                    </div>
                </div>
            </section>

            <!-- Main Content -->
            <section class="py-16">
                <div class="container mx-auto px-4">
                    <div class="grid md:grid-cols-3 gap-12">
                        <!-- Left Column: Description -->
                        <div class="md:col-span-2 space-y-8">
                            <div class="prose dark:prose-invert max-w-none">
                                <h2 class="text-3xl font-bold text-dark-900 dark:text-white mb-6">À propos du projet
                                </h2>
                                <div class="text-dark-600 dark:text-dark-300 whitespace-pre-line leading-relaxed">
                                    {{ project.description }}
                                </div>
                            </div>

                            <!-- Gallery -->
                            <div v-if="project.images && project.images.length > 0" class="mt-12">
                                <h3 class="text-2xl font-bold text-dark-900 dark:text-white mb-6">Galerie</h3>
                                <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    <div v-for="(img, index) in project.images" :key="index"
                                        class="rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
                                        <img :src="img.image"
                                            :alt="img.caption || `${project.title} image ${index + 1}`"
                                            class="w-full h-auto object-cover hover:scale-105 transition-transform duration-500" />
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Right Column: Info & Actions -->
                        <div class="space-y-8">
                            <div
                                class="bg-gray-50 dark:bg-dark-800 p-6 rounded-xl border border-gray-200 dark:border-dark-700 sticky top-24">
                                <h3 class="text-xl font-bold text-dark-900 dark:text-white mb-6">Informations</h3>

                                <div class="space-y-4 mb-8">
                                    <div v-if="project.category">
                                        <span
                                            class="text-sm text-dark-500 dark:text-dark-400 block mb-1">Catégorie</span>
                                        <span class="font-medium text-dark-900 dark:text-white">{{
                                            getCategoryLabel(project.category) }}</span>
                                    </div>

                                    <div v-if="project.completion_date">
                                        <span class="text-sm text-dark-500 dark:text-dark-400 block mb-1">Date de
                                            réalisation</span>
                                        <span class="font-medium text-dark-900 dark:text-white">{{
                                            formatDate(project.completion_date) }}</span>
                                    </div>
                                </div>

                                <div class="space-y-3">
                                    <a v-if="project.live_url" :href="project.live_url" target="_blank"
                                        rel="noopener noreferrer"
                                        class="block w-full py-3 px-4 bg-primary-600 hover:bg-primary-700 text-white text-center rounded-lg font-bold transition-colors shadow-lg shadow-primary-600/30">
                                        Voir le site en ligne
                                    </a>

                                    <a v-if="project.github_url" :href="project.github_url" target="_blank"
                                        rel="noopener noreferrer"
                                        class="block w-full py-3 px-4 bg-dark-800 hover:bg-dark-700 dark:bg-dark-700 dark:hover:bg-dark-600 text-white text-center rounded-lg font-bold transition-colors border border-dark-700">
                                        Voir le code source
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </section>
        </div>
    </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getProject } from '../api/portfolio'
import { useSEO } from '../composables/useSEO'
import { PORTFOLIO_CATEGORY_LABELS } from '../utils/constants'

const route = useRoute()
const project = ref(null)
const loading = ref(true)
const error = ref(null)

const getCategoryLabel = (category) => PORTFOLIO_CATEGORY_LABELS[category] || category

const formatDate = (dateString) => {
    if (!dateString) return ''
    return new Date(dateString).toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long'
    })
}

const loadProject = async () => {
    loading.value = true
    error.value = null
    try {
        const slug = route.params.slug
        const response = await getProject(slug)
        project.value = response.data

        // Update SEO
        useSEO(
            project.value.title,
            project.value.short_description,
            project.value.image_main || project.value.thumbnail
        )
    } catch (err) {
        // Erreur loguée via le message affiché dans le template
        if (import.meta.env.DEV) console.error('Erreur chargement projet:', err)
        error.value = "Impossible de charger le projet. Il n'existe peut-être pas ou a été déplacé."
    } finally {
        loading.value = false
    }
}

onMounted(loadProject)

// Reload if slug changes (e.g. navigation between projects)
watch(() => route.params.slug, loadProject)
</script>
