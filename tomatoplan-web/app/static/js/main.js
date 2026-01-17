/**
 * TomatoPlan Web - Main JavaScript
 */

// Utilitaires globaux
const TomatoPlan = {
    // Format de date française
    formatDate: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    },

    // Format de datetime française
    formatDateTime: function(dateString) {
        const date = new Date(dateString);
        return date.toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    },

    // Format monétaire
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('fr-FR', {
            style: 'currency',
            currency: 'EUR'
        }).format(amount);
    },

    // Afficher un message de notification
    showNotification: function(message, type = 'info') {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3`;
        alertDiv.style.zIndex = '9999';
        alertDiv.style.minWidth = '300px';
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alertDiv);

        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    },

    // Confirmer une action
    confirm: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },

    // Appel API générique
    api: async function(url, method = 'GET', data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            }
        };

        if (data && method !== 'GET') {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            const result = await response.json();

            if (!response.ok) {
                throw new Error(result.error || 'Erreur serveur');
            }

            return result;
        } catch (error) {
            console.error('API Error:', error);
            TomatoPlan.showNotification(error.message, 'danger');
            throw error;
        }
    },

    // Recherche globale
    search: async function(query, type = 'all') {
        if (query.length < 2) {
            return { results: {} };
        }

        return await TomatoPlan.api(`/api/search?q=${encodeURIComponent(query)}&type=${type}`);
    },

    // Export de données
    exportData: function(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};

// Initialisation au chargement
document.addEventListener('DOMContentLoaded', function() {
    // Activer les tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Activer les popovers Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-dismiss des alertes après 5 secondes
    setTimeout(() => {
        const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Recherche globale (si présente)
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        let searchTimeout;
        globalSearch.addEventListener('input', function(e) {
            clearTimeout(searchTimeout);
            const query = e.target.value;

            searchTimeout = setTimeout(async () => {
                if (query.length >= 2) {
                    const results = await TomatoPlan.search(query);
                    displaySearchResults(results);
                }
            }, 300);
        });
    }

    // Confirmation pour les actions de suppression
    const deleteButtons = document.querySelectorAll('[data-action="delete"]');
    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (!confirm('Êtes-vous sûr de vouloir supprimer cet élément ?')) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });

    // Auto-save pour les formulaires (optionnel)
    setupAutoSave();

    // Raccourcis clavier
    setupKeyboardShortcuts();
});

// Afficher les résultats de recherche
function displaySearchResults(results) {
    const container = document.getElementById('searchResults');
    if (!container) return;

    container.innerHTML = '';

    if (results.results.missions && results.results.missions.length > 0) {
        const section = document.createElement('div');
        section.innerHTML = '<h6>Missions</h6>';
        results.results.missions.forEach(mission => {
            const item = document.createElement('a');
            item.href = `/planning?date=${mission.date}`;
            item.className = 'list-group-item list-group-item-action';
            item.textContent = `${mission.date} ${mission.heure} - ${mission.voyage}`;
            section.appendChild(item);
        });
        container.appendChild(section);
    }

    // Ajouter d'autres types de résultats...
}

// Auto-save pour les formulaires
function setupAutoSave() {
    const forms = document.querySelectorAll('[data-autosave]');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                const formData = new FormData(form);
                localStorage.setItem(`autosave_${form.id}`, JSON.stringify(Object.fromEntries(formData)));
            });
        });

        // Restaurer les données sauvegardées
        const savedData = localStorage.getItem(`autosave_${form.id}`);
        if (savedData) {
            const data = JSON.parse(savedData);
            Object.keys(data).forEach(key => {
                const input = form.querySelector(`[name="${key}"]`);
                if (input) {
                    input.value = data[key];
                }
            });
        }
    });
}

// Raccourcis clavier
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K : Recherche globale
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.getElementById('globalSearch');
            if (searchInput) {
                searchInput.focus();
            }
        }

        // Echap : Fermer les modals
        if (e.key === 'Escape') {
            const modals = document.querySelectorAll('.modal.show');
            modals.forEach(modal => {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) {
                    bsModal.hide();
                }
            });
        }
    });
}

// Helper pour les tableaux triables
function makeSortable(tableId) {
    const table = document.getElementById(tableId);
    if (!table) return;

    const headers = table.querySelectorAll('th[data-sortable]');
    headers.forEach((header, index) => {
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="bi bi-arrow-down-up"></i>';

        header.addEventListener('click', function() {
            sortTable(table, index);
        });
    });
}

function sortTable(table, columnIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));

    const isAscending = table.getAttribute('data-sort-order') !== 'asc';

    rows.sort((a, b) => {
        const aValue = a.cells[columnIndex].textContent.trim();
        const bValue = b.cells[columnIndex].textContent.trim();

        if (!isNaN(aValue) && !isNaN(bValue)) {
            return isAscending ? aValue - bValue : bValue - aValue;
        }

        return isAscending
            ? aValue.localeCompare(bValue)
            : bValue.localeCompare(aValue);
    });

    rows.forEach(row => tbody.appendChild(row));

    table.setAttribute('data-sort-order', isAscending ? 'asc' : 'desc');
}

// Export global
window.TomatoPlan = TomatoPlan;
