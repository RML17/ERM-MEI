// datatables-config.js - Configurações para DataTables

/**
 * Configura os DataTables da aplicação com opções padronizadas
 */
function initializeDataTablesConfig() {
    // Se DataTables não estiver carregado, sair da função
    if (typeof $.fn.DataTable === 'undefined') {
        return;
    }

    // Configuração padrão para todos os DataTables
    $.extend(true, $.fn.dataTable.defaults, {
        language: {
            url: '//cdn.datatables.net/plug-ins/1.10.24/i18n/Portuguese-Brasil.json'
        },
        responsive: true,
        processing: true,
        pageLength: 10,
        lengthMenu: [[10, 25, 50, -1], [10, 25, 50, "Todos"]],
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
             '<"row"<"col-sm-12"tr>>' +
             '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
        buttons: [
            'copy', 'excel', 'pdf', 'print'
        ]
    });

    // Customização para tema escuro
    $.extend(true, $.fn.dataTable.defaults, {
        "initComplete": function(settings, json) {
            $(this).closest('.dataTables_wrapper').addClass('table-responsive');
            
            // Aplicar classes do Bootstrap para estilização
            $(this).closest('.dataTables_wrapper').find('.dataTables_length select').addClass('form-select form-select-sm');
            $(this).closest('.dataTables_wrapper').find('.dataTables_filter input').addClass('form-control form-control-sm');
            $(this).closest('.dataTables_wrapper').find('.dataTables_info').addClass('text-muted');
            
            // Ajustes para tema escuro
            $(this).closest('.dataTables_wrapper').find('.paginate_button').addClass('text-light');
        }
    });

    // Inicializar DataTables
    $('.datatable').each(function() {
        const tableOptions = {};
        
        // Verificar se é uma tabela de produtos
        if ($(this).hasClass('product-table')) {
            tableOptions.columnDefs = [
                { targets: -1, orderable: false, searchable: false } // Última coluna (ações)
            ];
        }
        
        // Verificar se é uma tabela de notas fiscais
        if ($(this).hasClass('invoice-table')) {
            tableOptions.order = [[4, 'desc']]; // Ordenar por data de emissão (decrescente)
            tableOptions.columnDefs = [
                { targets: -1, orderable: false, searchable: false } // Última coluna (ações)
            ];
        }
        
        // Verificar se é uma tabela de pagamentos
        if ($(this).hasClass('payment-table')) {
            tableOptions.order = [[3, 'asc']]; // Ordenar por data de vencimento (crescente)
            tableOptions.columnDefs = [
                { targets: -1, orderable: false, searchable: false }, // Última coluna (ações)
                { 
                    targets: 3, // Coluna de data de vencimento
                    render: function(data, type, row) {
                        // Destacar pagamentos vencidos
                        const dueDate = new Date(data);
                        const today = new Date();
                        today.setHours(0, 0, 0, 0);
                        
                        if (dueDate < today && row[4] !== 'Pago' && row[4] !== 'Cancelado') {
                            return '<span class="text-danger">' + data + '</span>';
                        }
                        return data;
                    }
                }
            ];
        }
        
        // Verificar se é uma tabela de movimentação de estoque
        if ($(this).hasClass('inventory-table')) {
            tableOptions.order = [[3, 'desc']]; // Ordenar por data de movimentação (decrescente)
            tableOptions.columnDefs = [
                { 
                    targets: 1, // Coluna tipo de movimento
                    render: function(data, type, row) {
                        if (data === 'entrada') {
                            return '<span class="badge bg-success">Entrada</span>';
                        } else {
                            return '<span class="badge bg-danger">Saída</span>';
                        }
                    }
                }
            ];
        }
        
        // Verificar se é uma tabela de auditoria
        if ($(this).hasClass('audit-table')) {
            tableOptions.order = [[5, 'desc']]; // Ordenar por timestamp (decrescente)
        }
        
        $(this).DataTable(tableOptions);
    });
}

// Inicializar configurações quando o documento estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    initializeDataTablesConfig();
});
