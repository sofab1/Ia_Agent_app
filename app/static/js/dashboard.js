document.addEventListener('DOMContentLoaded', function() {
    // Gestion du menu mobile
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            sidebar.classList.toggle('open');
        });
    }
    
    // Navigation entre les sections
    const navLinks = document.querySelectorAll('nav a');
    const contentSections = document.querySelectorAll('.content-section');
    const pageTitle = document.getElementById('page-title');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Ne pas traiter les liens externes (comme /chat ou /logout)
            if (this.getAttribute('href').startsWith('#')) {
                e.preventDefault();
                
                // Récupérer l'ID de la section
                const targetId = this.getAttribute('href').substring(1);
                const targetSection = document.getElementById(`${targetId}-content`);
                
                // Masquer toutes les sections
                contentSections.forEach(section => {
                    section.classList.add('hidden');
                });
                
                // Afficher la section cible
                if (targetSection) {
                    targetSection.classList.remove('hidden');
                    // Mettre à jour le titre de la page
                    if (pageTitle) {
                        pageTitle.textContent = this.textContent.trim();
                    }
                }
            }
        });
    });
    
    // Initialiser les graphiques
    initCharts();
    
    // Charger les données initiales
    loadDashboardData();
});

// Initialisation des graphiques avec Chart.js
function initCharts() {
    // Graphique Questions & Réponses
    const questionsCtx = document.getElementById('questionsChart');
    if (questionsCtx) {
        new Chart(questionsCtx, {
            type: 'line',
            data: {
                labels: Array.from({length: 30}, (_, i) => `Jour ${i+1}`),
                datasets: [
                    {
                        label: 'Questions',
                        data: generateRandomData(30, 50, 100),
                        borderColor: 'rgba(59, 130, 246, 0.8)',
                        backgroundColor: 'rgba(59, 130, 246, 0.2)',
                        tension: 0.4
                    },
                    {
                        label: 'Réponses',
                        data: generateRandomData(30, 45, 95),
                        borderColor: 'rgba(16, 185, 129, 0.8)',
                        backgroundColor: 'rgba(16, 185, 129, 0.2)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                }
            }
        });
    }
    
    // Graphique Catégories
    const categoriesCtx = document.getElementById('categoriesChart');
    if (categoriesCtx) {
        new Chart(categoriesCtx, {
            type: 'doughnut',
            data: {
                labels: ['Général', 'Technique', 'Produit', 'Support', 'Autre'],
                datasets: [{
                    data: [35, 25, 20, 15, 5],
                    backgroundColor: [
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)',
                        'rgba(107, 114, 128, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                    }
                }
            }
        });
    }
    
    // Initialiser les autres graphiques pour Analytics
    initAnalyticsCharts();
}

function initAnalyticsCharts() {
    // Graphique Questions Over Time
    const questionsOverTimeCtx = document.getElementById('questionsOverTimeChart');
    if (questionsOverTimeCtx) {
        new Chart(questionsOverTimeCtx, {
            type: 'bar',
            data: {
                labels: ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim'],
                datasets: [{
                    label: 'Questions par jour',
                    data: generateRandomData(7, 30, 80),
                    backgroundColor: 'rgba(59, 130, 246, 0.8)'
                }]
            },
            options: {
                responsive: true
            }
        });
    }
    
    // Graphique Response Times
    const responseTimesCtx = document.getElementById('responseTimesChart');
    if (responseTimesCtx) {
        new Chart(responseTimesCtx, {
            type: 'line',
            data: {
                labels: Array.from({length: 7}, (_, i) => `Jour ${i+1}`),
                datasets: [{
                    label: 'Temps de réponse moyen (ms)',
                    data: generateRandomData(7, 200, 800),
                    borderColor: 'rgba(245, 158, 11, 0.8)',
                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true
            }
        });
    }
    
    // Graphique Satisfaction
    const satisfactionCtx = document.getElementById('satisfactionChart');
    if (satisfactionCtx) {
        new Chart(satisfactionCtx, {
            type: 'pie',
            data: {
                labels: ['Très satisfait', 'Satisfait', 'Neutre', 'Insatisfait', 'Très insatisfait'],
                datasets: [{
                    data: [45, 30, 15, 7, 3],
                    backgroundColor: [
                        'rgba(16, 185, 129, 0.8)',
                        'rgba(59, 130, 246, 0.8)',
                        'rgba(107, 114, 128, 0.8)',
                        'rgba(245, 158, 11, 0.8)',
                        'rgba(239, 68, 68, 0.8)'
                    ]
                }]
            },
            options: {
                responsive: true
            }
        });
    }
}

// Fonction utilitaire pour générer des données aléatoires
function generateRandomData(length, min, max) {
    return Array.from({length}, () => Math.floor(Math.random() * (max - min + 1)) + min);
}

// Charger les données du tableau de bord depuis l'API
function loadDashboardData() {
    // Simuler le chargement des données (à remplacer par des appels API réels)
    fetch('/api/dashboard/stats')
        .then(response => {
            if (!response.ok) {
                throw new Error('Erreur lors du chargement des données');
            }
            return response.json();
        })
        .then(data => {
            updateDashboardStats(data);
        })
        .catch(error => {
            console.error('Erreur:', error);
            // Afficher un message d'erreur à l'utilisateur
        });
}

// Mettre à jour les statistiques du tableau de bord
function updateDashboardStats(response) {
    if (!response.success || !response.data) {
        console.error('Format de réponse invalide:', response);
        return;
    }
    
    const data = response.data;
    
    // 1. Mettre à jour les statistiques générales
    if (data.stats) {
        const stats = data.stats;
        document.getElementById('total-users').textContent = stats.total_users;
        document.getElementById('questions-today').textContent = stats.questions_today;
        document.getElementById('response-rate').textContent = stats.response_rate + '%';
        document.getElementById('error-rate').textContent = stats.error_rate + '%';
    }
    
    // 2. Mettre à jour les graphiques
    if (data.charts) {
        updateCharts(data.charts);
    }
    
    // 3. Mettre à jour la liste des questions récentes
    if (data.recent_questions) {
        updateRecentQuestions(data.recent_questions);
    }
    
    console.log('Données du tableau de bord mises à jour avec succès');
}

// Mettre à jour les graphiques avec les données de l'API
function updateCharts(chartData) {
    // Récupérer les instances de graphiques
    const questionsChart = Chart.getChart('questionsChart');
    const categoriesChart = Chart.getChart('categoriesChart');
    
    if (questionsChart && chartData.dates && chartData.questions && chartData.responses) {
        // Mettre à jour le graphique des questions et réponses
        questionsChart.data.labels = chartData.dates;
        questionsChart.data.datasets[0].data = chartData.questions;
        questionsChart.data.datasets[1].data = chartData.responses;
        questionsChart.update();
    }
    
    if (categoriesChart && chartData.categories) {
        // Mettre à jour le graphique des catégories
        const categories = chartData.categories;
        categoriesChart.data.labels = Object.keys(categories);
        categoriesChart.data.datasets[0].data = Object.values(categories);
        categoriesChart.update();
    }
}

// Mettre à jour la liste des questions récentes
function updateRecentQuestions(questions) {
    const recentQuestionsContainer = document.getElementById('recent-questions');
    if (!recentQuestionsContainer) return;
    
    // Vider le conteneur
    recentQuestionsContainer.innerHTML = '';
    
    // Ajouter chaque question
    questions.forEach(q => {
        const statusClass = getStatusClass(q.status);
        
        const questionItem = document.createElement('div');
        questionItem.className = 'bg-white p-4 rounded-lg shadow mb-3';
        questionItem.innerHTML = `
            <div class="flex justify-between items-center">
                <div>
                    <p class="font-medium">${q.user}</p>
                    <p class="text-gray-600">${q.question}</p>
                </div>
                <div class="text-right">
                    <span class="px-2 py-1 rounded text-xs ${statusClass}">${q.status}</span>
                    <p class="text-gray-500 text-sm mt-1">${q.time}</p>
                </div>
            </div>
        `;
        
        recentQuestionsContainer.appendChild(questionItem);
    });
}

// Obtenir la classe CSS en fonction du statut
function getStatusClass(status) {
    switch(status.toLowerCase()) {
        case 'répondu':
        case 'answered':
            return 'bg-green-100 text-green-800';
        case 'en attente':
        case 'pending':
            return 'bg-yellow-100 text-yellow-800';
        case 'erreur':
        case 'error':
            return 'bg-red-100 text-red-800';
        default:
            return 'bg-gray-100 text-gray-800';
    }
}
