// main.js - Funções gerais para o Sistema de Gestão Financeira

document.addEventListener('DOMContentLoaded', function() {
    // Toggle do sidebar
    const sidebarToggleBtn = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const contentWrapper = document.getElementById('contentWrapper');
    
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function() {
            sidebar.classList.toggle('collapsed');
            contentWrapper.classList.toggle('expanded');
            // Salvar preferência do usuário
            const sidebarState = sidebar.classList.contains('collapsed') ? 'collapsed' : 'expanded';
            localStorage.setItem('sidebarState', sidebarState);
        });
    }
    
    // Carregar preferência do usuário
    const savedSidebarState = localStorage.getItem('sidebarState');
    if (savedSidebarState === 'collapsed' && sidebar) {
        sidebar.classList.add('collapsed');
        contentWrapper.classList.add('expanded');
    }
    
    // Aplicar máscaras a campos
    applyInputMasks();
    
    // Inicializar tooltips do Bootstrap
    initializeTooltips();
    
    // Inicializar DataTables
    initializeDataTables();
    
    // Inicializar formulários dinâmicos
    initDynamicForms();
    
    // Inicializar alertas de confirmação
    initConfirmationAlerts();
    
    // Esconder alertas após um tempo
    autoHideAlerts();
});

// Aplicar máscaras a campos de entrada
function applyInputMasks() {
    // CPF/CNPJ
    const documentInputs = document.querySelectorAll('.mask-document');
    documentInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // Verificar se é CPF ou CNPJ com base no número de caracteres
            if (value.length <= 11) {
                // Formatar como CPF
                if (value.length > 9) {
                    value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
                } else if (value.length > 6) {
                    value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
                } else if (value.length > 3) {
                    value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
                }
            } else {
                // Formatar como CNPJ
                if (value.length > 12) {
                    value = value.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{1,2})/, '$1.$2.$3/$4-$5');
                } else if (value.length > 8) {
                    value = value.replace(/(\d{2})(\d{3})(\d{3})(\d{1,4})/, '$1.$2.$3/$4');
                } else if (value.length > 5) {
                    value = value.replace(/(\d{2})(\d{3})(\d{1,3})/, '$1.$2.$3');
                } else if (value.length > 2) {
                    value = value.replace(/(\d{2})(\d{1,3})/, '$1.$2');
                }
            }
            
            e.target.value = value;
        });
    });
    
    // CEP
    const cepInputs = document.querySelectorAll('.mask-cep');
    cepInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 5) {
                value = value.replace(/(\d{5})(\d{1,3})/, '$1-$2');
            }
            
            e.target.value = value;
        });
    });
    
    // Telefone
    const phoneInputs = document.querySelectorAll('.mask-phone');
    phoneInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            if (value.length > 10) {
                value = value.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
            } else if (value.length > 6) {
                value = value.replace(/(\d{2})(\d{4})(\d{1,4})/, '($1) $2-$3');
            } else if (value.length > 2) {
                value = value.replace(/(\d{2})(\d{1,4})/, '($1) $2');
            }
            
            e.target.value = value;
        });
    });
    
    // Moeda (R$)
    const currencyInputs = document.querySelectorAll('.mask-currency');
    currencyInputs.forEach(input => {
        input.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            
            // Converter para centavos
            value = (parseInt(value) / 100).toFixed(2);
            
            e.target.value = new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(value);
        });
        
        // Ao focar, remover a formatação e deixar apenas o número
        input.addEventListener('focus', function(e) {
            const value = e.target.value.replace(/[^\d,]/g, '').replace(',', '.');
            e.target.value = parseFloat(value || 0).toFixed(2).replace('.', ',');
        });
        
        // Ao perder o foco, formatar novamente
        input.addEventListener('blur', function(e) {
            const value = parseFloat(e.target.value.replace(/[^\d,]/g, '').replace(',', '.') || 0);
            e.target.value = new Intl.NumberFormat('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            }).format(value);
        });
    });
}

// Inicializar tooltips do Bootstrap
function initializeTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
}

// Inicializar DataTables
function initializeDataTables() {
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.datatable').each(function() {
            $(this).DataTable({
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.10.24/i18n/Portuguese-Brasil.json'
                },
                responsive: true,
                pageLength: 10,
                lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]]
            });
        });
    }
}

// Inicializar formulários dinâmicos
function initDynamicForms() {
    // Adicionar item de nota fiscal
    const addItemBtn = document.getElementById('addInvoiceItem');
    if (addItemBtn) {
        const itemsContainer = document.getElementById('invoiceItemsContainer');
        const itemTemplate = document.getElementById('invoiceItemTemplate');
        
        addItemBtn.addEventListener('click', function() {
            // Clonar o template
            const newItem = itemTemplate.content.cloneNode(true);
            const itemCount = itemsContainer.querySelectorAll('.invoice-item').length;
            
            // Atualizar IDs e nomes dos campos
            const inputs = newItem.querySelectorAll('select, input');
            inputs.forEach(input => {
                const name = input.getAttribute('name').replace('items-0', `items-${itemCount}`);
                input.setAttribute('name', name);
                input.setAttribute('id', name);
            });
            
            // Adicionar ao container
            itemsContainer.appendChild(newItem);
            
            // Adicionar evento para remover o item
            const removeBtn = itemsContainer.querySelector(`.invoice-item:nth-child(${itemCount + 1}) .remove-item-btn`);
            removeBtn.addEventListener('click', function() {
                this.closest('.invoice-item').remove();
                updateItemIndexes();
                calculateInvoiceTotal();
            });
            
            // Adicionar eventos de cálculo
            const newQuantityInput = itemsContainer.querySelector(`.invoice-item:nth-child(${itemCount + 1}) [name$="quantity"]`);
            const newPriceInput = itemsContainer.querySelector(`.invoice-item:nth-child(${itemCount + 1}) [name$="unit_price"]`);
            const newDiscountInput = itemsContainer.querySelector(`.invoice-item:nth-child(${itemCount + 1}) [name$="discount"]`);
            
            [newQuantityInput, newPriceInput, newDiscountInput].forEach(input => {
                input.addEventListener('input', function() {
                    calculateItemTotal(this.closest('.invoice-item'));
                    calculateInvoiceTotal();
                });
            });
        });
        
        // Calcula o total de um item
        function calculateItemTotal(itemElement) {
            const quantity = parseFloat(itemElement.querySelector('[name$="quantity"]').value) || 0;
            const price = parseFloat(itemElement.querySelector('[name$="unit_price"]').value) || 0;
            const discount = parseFloat(itemElement.querySelector('[name$="discount"]').value) || 0;
            
            const total = (quantity * price) - discount;
            itemElement.querySelector('.item-total').textContent = total.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL'
            });
        }
        
        // Calcula o total da nota
        function calculateInvoiceTotal() {
            const items = itemsContainer.querySelectorAll('.invoice-item');
            let total = 0;
            
            items.forEach(item => {
                const quantity = parseFloat(item.querySelector('[name$="quantity"]').value) || 0;
                const price = parseFloat(item.querySelector('[name$="unit_price"]').value) || 0;
                const discount = parseFloat(item.querySelector('[name$="discount"]').value) || 0;
                
                total += (quantity * price) - discount;
            });
            
            const totalElement = document.getElementById('invoiceTotal');
            if (totalElement) {
                totalElement.textContent = total.toLocaleString('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                });
            }
            
            // Calcular impostos se necessário
            calculateTaxes();
        }
        
        // Atualizar índices dos itens após remoção
        function updateItemIndexes() {
            const items = itemsContainer.querySelectorAll('.invoice-item');
            
            items.forEach((item, index) => {
                const inputs = item.querySelectorAll('select, input');
                inputs.forEach(input => {
                    const name = input.getAttribute('name').replace(/items-\d+/, `items-${index}`);
                    input.setAttribute('name', name);
                    input.setAttribute('id', name);
                });
            });
        }
        
        // Calcular impostos
        function calculateTaxes() {
            const calculateTaxesBtn = document.getElementById('calculateTaxes');
            if (!calculateTaxesBtn) return;
            
            const invoiceType = document.getElementById('type').value;
            const items = [];
            
            itemsContainer.querySelectorAll('.invoice-item').forEach(item => {
                const productId = parseInt(item.querySelector('[name$="product_id"]').value);
                const quantity = parseFloat(item.querySelector('[name$="quantity"]').value) || 0;
                const price = parseFloat(item.querySelector('[name$="unit_price"]').value) || 0;
                const discount = parseFloat(item.querySelector('[name$="discount"]').value) || 0;
                
                if (productId && quantity > 0 && price > 0) {
                    items.push({
                        product_id: productId,
                        quantity: quantity,
                        unit_price: price,
                        discount: discount
                    });
                }
            });
            
            if (items.length > 0) {
                fetch('/invoices/calculate-taxes', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        invoice_type: invoiceType,
                        items: items
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        const taxesContainer = document.getElementById('taxesContainer');
                        taxesContainer.innerHTML = '';
                        
                        let totalTax = 0;
                        
                        Object.entries(data.taxes).forEach(([taxType, taxInfo]) => {
                            const taxRow = document.createElement('div');
                            taxRow.className = 'row mb-2';
                            taxRow.innerHTML = `
                                <div class="col-4">${taxType}</div>
                                <div class="col-4">${(taxInfo.rate * 100).toFixed(2)}%</div>
                                <div class="col-4">${taxInfo.value.toLocaleString('pt-BR', {
                                    style: 'currency',
                                    currency: 'BRL'
                                })}</div>
                            `;
                            taxesContainer.appendChild(taxRow);
                            totalTax += taxInfo.value;
                        });
                        
                        const invoiceTotal = parseFloat(document.getElementById('invoiceTotal').textContent.replace(/[^\d,]/g, '').replace(',', '.')) || 0;
                        const grandTotal = invoiceTotal + totalTax;
                        
                        document.getElementById('taxTotal').textContent = totalTax.toLocaleString('pt-BR', {
                            style: 'currency',
                            currency: 'BRL'
                        });
                        
                        document.getElementById('grandTotal').textContent = grandTotal.toLocaleString('pt-BR', {
                            style: 'currency',
                            currency: 'BRL'
                        });
                    }
                })
                .catch(error => {
                    console.error('Erro ao calcular impostos:', error);
                });
            }
        }
        
        // Adicionar evento ao botão de calcular impostos
        const calculateTaxesBtn = document.getElementById('calculateTaxes');
        if (calculateTaxesBtn) {
            calculateTaxesBtn.addEventListener('click', calculateTaxes);
        }
        
        // Adicionar eventos aos itens existentes
        const existingItems = itemsContainer.querySelectorAll('.invoice-item');
        existingItems.forEach(item => {
            const quantityInput = item.querySelector('[name$="quantity"]');
            const priceInput = item.querySelector('[name$="unit_price"]');
            const discountInput = item.querySelector('[name$="discount"]');
            
            [quantityInput, priceInput, discountInput].forEach(input => {
                if (input) {
                    input.addEventListener('input', function() {
                        calculateItemTotal(item);
                        calculateInvoiceTotal();
                    });
                }
            });
            
            const removeBtn = item.querySelector('.remove-item-btn');
            if (removeBtn) {
                removeBtn.addEventListener('click', function() {
                    item.remove();
                    updateItemIndexes();
                    calculateInvoiceTotal();
                });
            }
        });
        
        // Calcular totais iniciais
        existingItems.forEach(item => {
            calculateItemTotal(item);
        });
        calculateInvoiceTotal();
    }
    
    // Tipo de nota alterando entidade (cliente/fornecedor)
    const invoiceTypeSelect = document.getElementById('type');
    if (invoiceTypeSelect) {
        invoiceTypeSelect.addEventListener('change', function() {
            updateEntityField();
        });
        
        function updateEntityField() {
            const entityIdField = document.getElementById('entity_id');
            const entityLabel = document.querySelector('label[for="entity_id"]');
            
            // Fazer uma requisição para obter as opções corretas
            fetch(`/api/entities?type=${invoiceTypeSelect.value}`)
                .then(response => response.json())
                .then(data => {
                    entityIdField.innerHTML = '';
                    
                    data.entities.forEach(entity => {
                        const option = document.createElement('option');
                        option.value = entity.id;
                        option.textContent = entity.name;
                        entityIdField.appendChild(option);
                    });
                    
                    if (invoiceTypeSelect.value === 'OUTBOUND') {
                        entityLabel.textContent = 'Cliente';
                    } else {
                        entityLabel.textContent = 'Fornecedor';
                    }
                })
                .catch(error => {
                    console.error('Erro ao atualizar entidades:', error);
                });
        }
        
        // Executar ao carregar
        if (invoiceTypeSelect.value) {
            updateEntityField();
        }
    }
    
    // Tipo de relatório alterando opções disponíveis
    const reportTypeSelect = document.getElementById('report_type');
    if (reportTypeSelect) {
        const invoiceOptions = document.getElementById('invoice_options');
        const dateOptions = document.getElementById('date_options');
        
        reportTypeSelect.addEventListener('change', function() {
            const value = this.value;
            
            // Esconder todas as opções
            document.querySelectorAll('.report-options').forEach(el => {
                el.classList.remove('show');
            });
            
            // Mostrar apenas as opções relevantes
            if (value === 'invoices' || value === 'financial') {
                invoiceOptions.classList.add('show');
                dateOptions.classList.add('show');
            } else if (value === 'inventory') {
                // Nenhuma opção adicional
            }
        });
        
        // Executar ao carregar
        if (reportTypeSelect.value) {
            const event = new Event('change');
            reportTypeSelect.dispatchEvent(event);
        }
    }
}

// Inicializar alertas de confirmação
function initConfirmationAlerts() {
    const confirmButtons = document.querySelectorAll('[data-confirm]');
    
    confirmButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });
}

// Esconder alertas após um tempo
function autoHideAlerts() {
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, 5000);
    });
}

// Funções utilitárias
function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function formatDateTime(dateTimeString) {
    const date = new Date(dateTimeString);
    return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR');
}

// Exibir modal de carregamento
function showLoading() {
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        const modal = new bootstrap.Modal(loadingModal);
        modal.show();
    } else {
        const modalHtml = `
            <div class="modal fade" id="loadingModal" tabindex="-1" aria-hidden="true" data-bs-backdrop="static" data-bs-keyboard="false">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content">
                        <div class="modal-body text-center py-4">
                            <div class="spinner-border text-primary mb-3" role="status">
                                <span class="visually-hidden">Carregando...</span>
                            </div>
                            <h5>Processando, por favor aguarde...</h5>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
        modal.show();
    }
}

// Esconder modal de carregamento
function hideLoading() {
    const loadingModal = document.getElementById('loadingModal');
    if (loadingModal) {
        const modal = bootstrap.Modal.getInstance(loadingModal);
        if (modal) {
            modal.hide();
        }
    }
}
