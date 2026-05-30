// charts.js - Configurações de gráficos para o Sistema de Gestão Financeira

/**
 * Inicializa os gráficos do dashboard
 */
function initDashboardCharts() {
    // Gráfico de receitas vs despesas (substitui o gráfico de vendas)
    initRevenueExpenseChart();
    
    // Gráfico de status das notas fiscais
    initInvoiceStatusChart();
    
    // Gráfico de estoque
    initInventoryChart();
    
    // Gráfico de produtos mais vendidos
    initTopProductsChart();
}

/**
 * Inicializa o gráfico de receitas vs despesas
 */
function initRevenueExpenseChart() {
    const chartCanvas = document.getElementById('revenueExpenseChart');
    
    if (chartCanvas) {
        // Obter dados do elemento data
        const labels = JSON.parse(chartCanvas.getAttribute('data-labels') || '[]');
        const income = JSON.parse(chartCanvas.getAttribute('data-income') || '[]');
        const expense = JSON.parse(chartCanvas.getAttribute('data-expense') || '[]');
        
        // Criar o gráfico
        new Chart(chartCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Receitas (R$)',
                        data: income,
                        backgroundColor: 'rgba(40, 167, 69, 0.6)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Despesas (R$)',
                        data: expense,
                        backgroundColor: 'rgba(220, 53, 69, 0.6)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Análise Financeira dos Últimos 6 Meses',
                        color: '#fff'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('pt-BR', {
                                        style: 'currency',
                                        currency: 'BRL'
                                    }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('pt-BR', {
                                    style: 'currency',
                                    currency: 'BRL',
                                    maximumSignificantDigits: 3
                                }).format(value);
                            },
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }
}

/**
 * Inicializa o gráfico de produtos mais vendidos
 */
function initTopProductsChart() {
    const topProductsCanvas = document.getElementById('topProductsChart');
    
    if (topProductsCanvas) {
        // Obter dados do elemento data
        const labels = JSON.parse(topProductsCanvas.getAttribute('data-labels') || '[]');
        const quantities = JSON.parse(topProductsCanvas.getAttribute('data-quantities') || '[]');
        const values = JSON.parse(topProductsCanvas.getAttribute('data-values') || '[]');
        
        // Criar o gráfico
        new Chart(topProductsCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Quantidade Vendida',
                        data: quantities,
                        backgroundColor: 'rgba(54, 162, 235, 0.6)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Valor Total (R$)',
                        data: values,
                        backgroundColor: 'rgba(255, 159, 64, 0.6)',
                        borderColor: 'rgba(255, 159, 64, 1)',
                        borderWidth: 1,
                        type: 'line',
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                indexAxis: 'y',  // Gráfico horizontal
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Produtos Mais Vendidos',
                        color: '#fff'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.datasetIndex === 0) {
                                    // Quantidade
                                    label += context.parsed.x.toFixed(2);
                                } else if (context.datasetIndex === 1) {
                                    // Valor
                                    label += new Intl.NumberFormat('pt-BR', {
                                        style: 'currency',
                                        currency: 'BRL'
                                    }).format(context.parsed.x);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: false,
                        position: 'right',
                        beginAtZero: true
                    }
                }
            }
        });
    }
}

/**
 * Inicializa o gráfico de status das notas fiscais
 */
function initInvoiceStatusChart() {
    const statusChartCanvas = document.getElementById('invoiceStatusChart');
    
    if (statusChartCanvas) {
        // Obter dados do elemento
        const statusData = {};
        const statusElement = document.getElementById('invoiceStatusData');
        
        if (statusElement) {
            const statuses = JSON.parse(statusElement.getAttribute('data-statuses') || '{}');
            Object.keys(statuses).forEach(key => {
                statusData[key] = statuses[key];
            });
        }
        
        // Preparar dados para o gráfico de pizza
        const labels = [];
        const values = [];
        const backgroundColors = [];
        
        // Cores para cada status
        const statusColors = {
            'DRAFT': 'rgba(108, 117, 125, 0.7)',
            'PENDING': 'rgba(255, 193, 7, 0.7)',
            'ISSUED': 'rgba(23, 162, 184, 0.7)',
            'CANCELED': 'rgba(220, 53, 69, 0.7)',
            'APPROVED': 'rgba(40, 167, 69, 0.7)'
        };
        
        Object.keys(statusData).forEach(status => {
            if (statusData[status] > 0) {
                labels.push(status);
                values.push(statusData[status]);
                backgroundColors.push(statusColors[status] || 'rgba(54, 162, 235, 0.7)');
            }
        });
        
        // Criar o gráfico
        new Chart(statusChartCanvas, {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: backgroundColors,
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Status das Notas Fiscais',
                        color: '#fff'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = Math.round((value / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * Inicializa o gráfico de estoque
 */
function initInventoryChart() {
    const inventoryChartCanvas = document.getElementById('inventoryChart');
    
    if (inventoryChartCanvas) {
        // Obter dados do elemento
        const lowStockElement = document.getElementById('lowStockData');
        if (!lowStockElement) return;
        
        const rawProducts = JSON.parse(lowStockElement.getAttribute('data-products') || '[]');
        
        // Preparar dados para o gráfico
        const labels = [];
        const currentStock = [];
        const minStock = [];
        
        rawProducts.forEach(item => {
            if (item.product && item.product.name) {
                // Limitar o tamanho do nome do produto para exibição
                let productName = item.product.name;
                if (productName.length > 20) {
                    productName = productName.substring(0, 17) + '...';
                }
                
                labels.push(productName);
                currentStock.push(item.current_stock);
                minStock.push(item.min_stock || item.product.min_stock);
            }
        });
        
        // Criar o gráfico
        new Chart(inventoryChartCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Estoque Atual',
                        data: currentStock,
                        backgroundColor: 'rgba(54, 162, 235, 0.7)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Estoque Mínimo',
                        data: minStock,
                        backgroundColor: 'rgba(255, 99, 132, 0.7)',
                        borderColor: 'rgba(255, 99, 132, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Produtos com Estoque Baixo',
                        color: '#fff'
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }
}

/**
 * Inicializa o gráfico financeiro para a página de relatórios
 * @param {Array} data Array de objetos com dados financeiros
 * @param {string} elementId ID do elemento canvas
 */
function initFinancialChart(data, elementId) {
    const chartCanvas = document.getElementById(elementId);
    
    if (chartCanvas && data) {
        // Preparar dados para o gráfico
        const labels = data.map(item => item.label);
        const incomeData = data.map(item => item.income);
        const expenseData = data.map(item => item.expense);
        
        // Criar o gráfico
        new Chart(chartCanvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Receitas',
                        data: incomeData,
                        backgroundColor: 'rgba(40, 167, 69, 0.7)',
                        borderColor: 'rgba(40, 167, 69, 1)',
                        borderWidth: 1
                    },
                    {
                        label: 'Despesas',
                        data: expenseData,
                        backgroundColor: 'rgba(220, 53, 69, 0.7)',
                        borderColor: 'rgba(220, 53, 69, 1)',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: '#fff'
                        }
                    },
                    title: {
                        display: true,
                        text: 'Balanço Financeiro',
                        color: '#fff'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += new Intl.NumberFormat('pt-BR', {
                                        style: 'currency',
                                        currency: 'BRL'
                                    }).format(context.parsed.y);
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return new Intl.NumberFormat('pt-BR', {
                                    style: 'currency',
                                    currency: 'BRL',
                                    maximumSignificantDigits: 3
                                }).format(value);
                            },
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    x: {
                        ticks: {
                            color: '#fff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }
}

// Inicializar gráficos quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    initDashboardCharts();
});
