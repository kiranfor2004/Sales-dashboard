// Function to format currency
function formatCurrency(value) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0
    }).format(value);
}

// Function to format large numbers
function formatLargeNumber(value) {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + 'M';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(1) + 'K';
    }
    return value.toFixed(0);
}

// Function to calculate percentage change
function calculateChange(current, previous) {
    if (previous === 0) return 0;
    return ((current - previous) / previous * 100);
}

// Fetch and display Overall Sales Performance
fetch('http://127.0.0.1:5000/api/overall_sales_performance')
    .then(response => response.json())
    .then(data => {
        // Update the grand total KPI card
        document.getElementById('grand-total').textContent = formatCurrency(data.grand_total);
        document.getElementById('revenue-streams').textContent = `${data.revenue_streams.length} Revenue Streams`;
        document.getElementById('revenue-streams').className = 'kpi-change positive';

        // Create bar chart for overall sales performance
        const overallSalesTrace = {
            x: data.revenue_streams,
            y: data.total_amounts,
            type: 'bar',
            name: 'Revenue by Stream',
            marker: {
                color: ['#2196F3', '#4CAF50', '#FF9800'],
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            },
            text: data.total_amounts.map((amount, index) => 
                `${formatCurrency(amount)}<br>(${data.percentages[index].toFixed(1)}%)`
            ),
            textposition: 'outside',
            textfont: { size: 11, color: '#333' }
        };

        const layout = {
            title: {
                text: '',
                font: { size: 16, color: '#333' }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Segoe UI, Arial, sans-serif', color: '#333' },
            xaxis: {
                title: { text: 'Revenue Streams', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                gridcolor: 'rgba(0,0,0,0.1)'
            },
            yaxis: {
                title: { text: 'Total Sales Amount ($)', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                gridcolor: 'rgba(0,0,0,0.1)',
                tickformat: ',.0f'
            },
            showlegend: false,
            annotations: [
                {
                    text: `Grand Total: ${formatCurrency(data.grand_total)}`,
                    showarrow: false,
                    x: 0.5,
                    y: 1.05,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    font: { size: 14, color: '#333', weight: 'bold' },
                    bgcolor: 'rgba(156, 39, 176, 0.1)',
                    bordercolor: '#9C27B0',
                    borderwidth: 1
                }
            ],
            margin: { t: 40, r: 20, b: 80, l: 80 }
        };

        Plotly.newPlot('overall-sales-container', [overallSalesTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching overall sales performance data:', error);
        document.getElementById('grand-total').textContent = 'Error';
        document.getElementById('revenue-streams').textContent = 'Error loading data';
    });

// Fetch and display Sales Mix pie chart
fetch('http://127.0.0.1:5000/api/sales_mix')
    .then(response => response.json())
    .then(data => {
        // Create professional color palette for pie chart
        const colors = [
            '#1e3c72', '#2196F3', '#4CAF50', '#FF9800', '#9C27B0', 
            '#00BCD4', '#795548', '#607D8B', '#E91E63', '#FFC107',
            '#8BC34A', '#FF5722', '#673AB7', '#009688', '#CDDC39'
        ];

        const salesMixTrace = {
            values: data.percentages,
            labels: data.item_types,
            type: 'pie',
            hole: 0.4, // Donut chart for modern look
            marker: {
                colors: colors.slice(0, data.item_types.length),
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 2
                }
            },
            textinfo: 'label+percent',
            textfont: { size: 11, color: 'white', family: 'Segoe UI, Arial, sans-serif' },
            hovertemplate: '<b>%{label}</b><br>' +
                          'Sales: %{customdata}<br>' +
                          'Share: %{percent}<br>' +
                          '<extra></extra>',
            customdata: data.retail_sales.map(sales => formatCurrency(sales))
        };

        const layout = {
            title: {
                text: '',
                font: { size: 16, color: '#333' }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Segoe UI, Arial, sans-serif', color: '#333' },
            showlegend: true,
            legend: {
                orientation: 'v',
                y: 0.5,
                x: 1.05,
                xanchor: 'left',
                yanchor: 'middle',
                font: { size: 10 }
            },
            annotations: [
                {
                    text: `<b>Total Retail<br>Sales</b><br>${formatCurrency(data.total_retail_sales)}`,
                    showarrow: false,
                    x: 0.5,
                    y: 0.5,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    yanchor: 'middle',
                    font: { size: 14, color: '#333' },
                    align: 'center'
                },
                {
                    text: `Top Contributor: <b>${data.top_contributor}</b> (${data.top_percentage.toFixed(1)}%)`,
                    showarrow: false,
                    x: 0.5,
                    y: -0.1,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    font: { size: 12, color: '#666' }
                }
            ],
            margin: { t: 20, r: 120, b: 60, l: 20 }
        };

        Plotly.newPlot('sales-mix-container', [salesMixTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching sales mix data:', error);
    });

// Fetch and display Top 10 Selling Items
fetch('http://127.0.0.1:5000/api/top_selling_items')
    .then(response => response.json())
    .then(data => {
        console.log('Top selling items data:', data);
        
        if (data.error) {
            console.error('Backend error:', data.error);
            return;
        }
        
        // Create color mapping based on performance tiers
        const colors = data.performance_tiers.map(tier => {
            switch(tier) {
                case 'Star Performer': return '#FFD700'; // Gold
                case 'Strong Performer': return '#C0C0C0'; // Silver
                case 'Good Performer': return '#CD7F32'; // Bronze
                default: return '#4CAF50';
            }
        });

        const topSellingTrace = {
            x: data.retail_sales,
            y: data.display_labels || data.item_codes, // Use display labels if available
            type: 'bar',
            orientation: 'h',
            name: 'Retail Sales',
            marker: {
                color: colors,
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            },
            text: data.retail_sales.map((sales, index) => 
                `#${data.ranks[index]} - ${formatCurrency(sales)}`
            ),
            textposition: 'outside',
            textfont: { size: 10, color: '#333' },
            hovertemplate: '<b>%{y}</b><br>' +
                          'Rank: #%{customdata}<br>' +
                          'Sales: %{x:$,.2f}<br>' +
                          '<extra></extra>',
            customdata: data.ranks
        };

        const layout = {
            title: {
                text: '',
                font: { size: 16, color: '#333' }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Segoe UI, Arial, sans-serif', color: '#333' },
            xaxis: {
                title: { text: 'Retail Sales ($)', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                gridcolor: 'rgba(0,0,0,0.1)',
                tickformat: ',.0f'
            },
            yaxis: {
                title: { text: 'Item Code', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666', size: 9 },
                gridcolor: 'rgba(0,0,0,0.1)',
                automargin: true
            },
            showlegend: false,
            annotations: [
                {
                    text: `🥇 Best Item: <b>${data.best_item}</b> (${formatCurrency(data.best_sales)})<br>` +
                          `🏆 Top 10 Total: ${formatCurrency(data.top_10_total)} (${data.top_10_percentage.toFixed(1)}% of total)`,
                    showarrow: false,
                    x: 0.98,
                    y: 0.02,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'right',
                    yanchor: 'bottom',
                    font: { size: 11, color: '#666' },
                    bgcolor: 'rgba(255,255,255,0.9)',
                    bordercolor: 'rgba(0,0,0,0.1)',
                    borderwidth: 1,
                    align: 'left'
                }
            ],
            margin: { t: 20, r: 20, b: 80, l: 150 }
        };

        Plotly.newPlot('top-selling-container', [topSellingTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching top selling items data:', error);
    });

// Fetch and display KPI data
fetch('http://127.0.0.1:5000/api/kpi_data')
    .then(response => response.json())
    .then(data => {
        // Update KPI cards
        const currentRetail = data.current_month.values[0];
        const previousRetail = data.previous_month.values[0];
        const currentWarehouse = data.current_month.values[1];
        const previousWarehouse = data.previous_month.values[1];
        
        // Update retail KPI
        document.getElementById('current-retail').textContent = formatCurrency(currentRetail);
        const retailChange = calculateChange(currentRetail, previousRetail);
        const retailChangeElement = document.getElementById('retail-change');
        retailChangeElement.textContent = `${retailChange > 0 ? '+' : ''}${retailChange.toFixed(1)}% from last month`;
        retailChangeElement.className = `kpi-change ${retailChange >= 0 ? 'positive' : 'negative'}`;
        
        // Update warehouse KPI
        document.getElementById('current-warehouse').textContent = formatCurrency(currentWarehouse);
        const warehouseChange = calculateChange(currentWarehouse, previousWarehouse);
        const warehouseChangeElement = document.getElementById('warehouse-change');
        warehouseChangeElement.textContent = `${warehouseChange > 0 ? '+' : ''}${warehouseChange.toFixed(1)}% from last month`;
        warehouseChangeElement.className = `kpi-change ${warehouseChange >= 0 ? 'positive' : 'negative'}`;

        // Create KPI chart with professional colors
        const currentMonthTrace = {
            x: data.labels,
            y: data.current_month.values,
            name: data.current_month.name,
            type: 'bar',
            marker: {
                color: ['#2196F3', '#FF9800'],
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            }
        };

        const previousMonthTrace = {
            x: data.labels,
            y: data.previous_month.values,
            name: data.previous_month.name,
            type: 'bar',
            marker: {
                color: ['rgba(33, 150, 243, 0.6)', 'rgba(255, 152, 0, 0.6)'],
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            }
        };

        const layout = {
            title: {
                text: '',
                font: { size: 16, color: '#333' }
            },
            barmode: 'group',
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Segoe UI, Arial, sans-serif', color: '#333' },
            xaxis: {
                title: { text: 'Sales Type', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                gridcolor: 'rgba(0,0,0,0.1)'
            },
            yaxis: {
                title: { text: 'Sales Amount ($)', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                gridcolor: 'rgba(0,0,0,0.1)',
                tickformat: ',.0f'
            },
            legend: {
                orientation: window.innerWidth < 768 ? 'h' : 'h',
                y: window.innerWidth < 768 ? -0.3 : -0.2,
                x: 0.5,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: 'rgba(0,0,0,0.1)',
                borderwidth: 1
            },
            margin: { t: 30, r: 20, b: window.innerWidth < 768 ? 120 : 100, l: 80 }
        };

        Plotly.newPlot('kpi-chart-container', [currentMonthTrace, previousMonthTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching KPI data:', error);
        document.getElementById('retail-change').textContent = 'Error loading data';
        document.getElementById('warehouse-change').textContent = 'Error loading data';
    });

// Fetch and display sales by item type with stacked bar chart
fetch('http://127.0.0.1:5000/api/sales_by_item_type')
    .then(response => response.json())
    .then(data => {
        // Create stacked bar chart traces for each sales component
        const retailSalesTrace = {
            x: data.item_types,
            y: data.retail_sales,
            name: 'Retail Sales',
            type: 'bar',
            marker: {
                color: '#2196F3',
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            }
        };

        const retailTransfersTrace = {
            x: data.item_types,
            y: data.retail_transfers,
            name: 'Retail Transfers',
            type: 'bar',
            marker: {
                color: '#4CAF50',
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            }
        };

        const warehouseSalesTrace = {
            x: data.item_types,
            y: data.warehouse_sales,
            name: 'Warehouse Sales',
            type: 'bar',
            marker: {
                color: '#FF9800',
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            }
        };

        const layout = {
            title: {
                text: '',
                font: { size: 16, color: '#333' }
            },
            barmode: 'stack',
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Segoe UI, Arial, sans-serif', color: '#333' },
            xaxis: {
                title: { text: 'Product Categories', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                tickangle: -45,
                gridcolor: 'rgba(0,0,0,0.1)'
            },
            yaxis: {
                title: { text: 'Total Sales Amount ($)', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                gridcolor: 'rgba(0,0,0,0.1)',
                tickformat: ',.0f'
            },
            legend: {
                orientation: window.innerWidth < 768 ? 'h' : 'v',
                y: window.innerWidth < 768 ? -0.25 : 1,
                x: window.innerWidth < 768 ? 0.5 : 1.02,
                xanchor: window.innerWidth < 768 ? 'center' : 'left',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: 'rgba(0,0,0,0.1)',
                borderwidth: 1,
                font: { size: 12 }
            },
            margin: { 
                t: 20, 
                r: window.innerWidth < 768 ? 20 : 120, 
                b: window.innerWidth < 768 ? 160 : 140, 
                l: 80 
            },
            annotations: [
                {
                    text: `Total Categories: ${data.item_types.length} | Highest Performer: ${data.item_types[0]}`,
                    showarrow: false,
                    x: 0.5,
                    y: window.innerWidth < 768 ? -0.35 : -0.25,
                    xref: 'paper',
                    yref: 'paper',
                    xanchor: 'center',
                    font: { size: 12, color: '#666' }
                }
            ]
        };

        Plotly.newPlot('chart-container', [retailSalesTrace, retailTransfersTrace, warehouseSalesTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching sales by item type data:', error);
    });

// Fetch and display sales transfer ratio
fetch('http://127.0.0.1:5000/api/sales_transfer_ratio')
    .then(response => response.json())
    .then(data => {
        // Create color mapping based on efficiency categories
        const colors = data.transfer_ratios.map(ratio => {
            if (ratio === 0) return '#9E9E9E'; // Gray for no transfers
            if (ratio >= 0.8 && ratio <= 1.2) return '#4CAF50'; // Green for efficient
            if (ratio > 1.2) return '#FF9800'; // Orange for high sales/low transfers
            return '#F44336'; // Red for low sales/high transfers
        });

        const transferRatioTrace = {
            x: data.item_types,
            y: data.transfer_ratios,
            type: 'bar',
            name: 'Sales Transfer Ratio',
            marker: {
                color: colors,
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            },
            text: data.transfer_ratios.map((ratio, index) => 
                `${ratio.toFixed(2)}<br>${data.efficiency_categories[index]}`
            ),
            textposition: 'outside',
            textfont: { size: 10 }
        };

        const layout = {
            title: {
                text: '',
                font: { size: 16, color: '#333' }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Segoe UI, Arial, sans-serif', color: '#333' },
            xaxis: {
                title: { text: 'Product Categories', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                tickangle: -45,
                gridcolor: 'rgba(0,0,0,0.1)'
            },
            yaxis: {
                title: { text: 'Sales Transfer Ratio', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                gridcolor: 'rgba(0,0,0,0.1)',
                tickformat: '.2f'
            },
            shapes: [
                {
                    type: 'line',
                    x0: -0.5,
                    x1: data.item_types.length - 0.5,
                    y0: 1,
                    y1: 1,
                    line: {
                        color: '#4CAF50',
                        width: 2,
                        dash: 'dash'
                    }
                },
                {
                    type: 'rect',
                    x0: -0.5,
                    x1: data.item_types.length - 0.5,
                    y0: 0.8,
                    y1: 1.2,
                    fillcolor: 'rgba(76, 175, 80, 0.1)',
                    line: { width: 0 }
                }
            ],
            annotations: [
                {
                    x: data.item_types.length / 2,
                    y: 1.05,
                    text: 'Optimal Efficiency Zone (0.8 - 1.2)',
                    showarrow: false,
                    font: { size: 12, color: '#4CAF50' },
                    bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: '#4CAF50',
                    borderwidth: 1
                }
            ],
            showlegend: false,
            margin: { t: 30, r: 20, b: 120, l: 80 }
        };

        Plotly.newPlot('transfer-ratio-container', [transferRatioTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching sales transfer ratio data:', error);
    });

// Fetch and display Month-over-Month Sales Growth
fetch('http://127.0.0.1:5000/api/month_over_month_growth')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        // Create line chart for month-over-month growth
        const growthTrace = {
            x: data.dates,
            y: data.growth_rates,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Growth Rate (%)',
            line: {
                color: '#2196F3',
                width: 3,
                shape: 'spline'
            },
            marker: {
                color: data.growth_rates.map(rate => {
                    if (rate > 10) return '#4CAF50';  // High Growth - Green
                    if (rate >= 5) return '#8BC34A';  // Moderate Growth - Light Green
                    if (rate >= -5) return '#FFC107'; // Stable - Amber
                    if (rate >= -10) return '#FF9800'; // Moderate Decline - Orange
                    return '#F44336'; // Significant Decline - Red
                }),
                size: 8,
                line: {
                    color: '#ffffff',
                    width: 2
                }
            },
            text: data.growth_rates.map((rate, index) => 
                `${data.dates[index]}<br>Growth: ${rate.toFixed(1)}%<br>Current: ${formatCurrency(data.current_sales[index])}<br>Previous: ${formatCurrency(data.previous_sales[index])}`
            ),
            hovertemplate: '%{text}<extra></extra>'
        };

        // Add horizontal reference lines for different growth zones
        const shapes = [
            {
                type: 'line',
                x0: data.dates[0],
                x1: data.dates[data.dates.length - 1],
                y0: 0,
                y1: 0,
                line: {
                    color: 'rgba(0,0,0,0.3)',
                    width: 2,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: data.dates[0],
                x1: data.dates[data.dates.length - 1],
                y0: 10,
                y1: 10,
                line: {
                    color: 'rgba(76, 175, 80, 0.3)',
                    width: 1,
                    dash: 'dot'
                }
            },
            {
                type: 'line',
                x0: data.dates[0],
                x1: data.dates[data.dates.length - 1],
                y0: -10,
                y1: -10,
                line: {
                    color: 'rgba(244, 67, 54, 0.3)',
                    width: 1,
                    dash: 'dot'
                }
            }
        ];

        const layout = {
            title: {
                text: `Average Growth: ${data.metrics.average_growth_rate.toFixed(1)}% | Latest: ${data.metrics.latest_growth_rate.toFixed(1)}%`,
                font: { size: 14, color: '#333' }
            },
            xaxis: {
                title: 'Month',
                gridcolor: 'rgba(0,0,0,0.1)',
                showgrid: true,
                tickangle: -45
            },
            yaxis: {
                title: 'Growth Rate (%)',
                gridcolor: 'rgba(0,0,0,0.1)',
                showgrid: true,
                zeroline: true,
                zerolinecolor: 'rgba(0,0,0,0.3)',
                zerolinewidth: 2
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            shapes: shapes,
            annotations: [
                {
                    x: data.dates[Math.floor(data.dates.length * 0.8)],
                    y: 15,
                    text: 'High Growth Zone (>10%)',
                    showarrow: false,
                    font: { size: 10, color: '#4CAF50' },
                    bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: '#4CAF50',
                    borderwidth: 1
                },
                {
                    x: data.dates[Math.floor(data.dates.length * 0.2)],
                    y: -15,
                    text: 'Decline Zone (<-10%)',
                    showarrow: false,
                    font: { size: 10, color: '#F44336' },
                    bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: '#F44336',
                    borderwidth: 1
                }
            ],
            showlegend: false,
            margin: { t: 40, r: 20, b: 80, l: 60 }
        };

        Plotly.newPlot('month-growth-container', [growthTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching month-over-month growth data:', error);
    });

// Fetch and display Inventory Turnover Rate
fetch('http://127.0.0.1:5000/api/inventory_turnover_rate')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        // Create gauge chart for inventory turnover rate
        const gaugeTrace = {
            type: "indicator",
            mode: "gauge+number+delta",
            value: data.turnover_rate,
            domain: { x: [0, 1], y: [0, 1] },
            title: { 
                text: `<b>${data.performance_category} Performance</b><br><span style='font-size:12px;color:#666'>Current Rate: ${data.turnover_rate.toFixed(2)}</span>`,
                font: { size: 16, color: "#333" }
            },
            delta: { 
                reference: data.benchmarks.good, 
                increasing: { color: "#4CAF50" },
                decreasing: { color: "#F44336" },
                font: { size: 14 }
            },
            gauge: {
                axis: { 
                    range: [null, 6], 
                    tickwidth: 1, 
                    tickcolor: "#333",
                    tickfont: { size: 12 }
                },
                bar: { 
                    color: data.performance_color,
                    thickness: 0.3
                },
                bgcolor: "white",
                borderwidth: 2,
                bordercolor: "#333",
                steps: [
                    { range: [0, 0.5], color: "rgba(244, 67, 54, 0.2)" },
                    { range: [0.5, 1.5], color: "rgba(255, 152, 0, 0.2)" },
                    { range: [1.5, 3.0], color: "rgba(255, 193, 7, 0.2)" },
                    { range: [3.0, 5.0], color: "rgba(139, 195, 74, 0.2)" },
                    { range: [5.0, 6], color: "rgba(76, 175, 80, 0.2)" }
                ],
                threshold: {
                    line: { color: "#333", width: 4 },
                    thickness: 0.75,
                    value: data.benchmarks.good
                }
            }
        };

        const layout = {
            width: 400,
            height: 300,
            margin: { t: 50, b: 30, l: 30, r: 30 },
            paper_bgcolor: "rgba(0,0,0,0)",
            plot_bgcolor: "rgba(0,0,0,0)",
            font: { color: "#333", family: "Arial, sans-serif" },
            annotations: [
                {
                    x: 0.5,
                    y: 0.1,
                    text: `<b>Benchmarks:</b><br>Excellent: ≥5.0 | Good: ≥3.0 | Average: ≥1.5 | Poor: ≥0.5`,
                    showarrow: false,
                    font: { size: 10, color: "#666" },
                    xanchor: 'center',
                    bgcolor: 'rgba(255,255,255,0.8)',
                    bordercolor: '#ddd',
                    borderwidth: 1
                },
                {
                    x: 0.5,
                    y: -0.1,
                    text: `<b>Efficiency Analysis:</b><br>${data.efficiency_metrics.efficient_categories}/${data.efficiency_metrics.total_categories} categories performing well (${data.efficiency_metrics.efficiency_percentage.toFixed(0)}%)`,
                    showarrow: false,
                    font: { size: 10, color: "#333" },
                    xanchor: 'center',
                    bgcolor: 'rgba(255,255,255,0.9)',
                    bordercolor: '#4CAF50',
                    borderwidth: 1
                }
            ]
        };

        Plotly.newPlot('inventory-turnover-container', [gaugeTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching inventory turnover data:', error);
    });
