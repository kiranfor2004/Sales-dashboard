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
                orientation: 'h',
                x: 0.5,
                y: -0.15,
                xanchor: 'center',
                yanchor: 'top',
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
            margin: { t: 20, r: 20, b: 80, l: 20 }
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
                orientation: 'h',
                y: -0.2,
                x: 0.5,
                xanchor: 'center',
                yanchor: 'top',
                bgcolor: 'rgba(255,255,255,0.9)',
                bordercolor: 'rgba(0,0,0,0.1)',
                borderwidth: 1,
                font: { size: 12 }
            },
            margin: { 
                t: 20, 
                r: 20, 
                b: 120, 
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
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        // Create line chart for transfer ratio over time
        const transferRatioTrace = {
            x: data.monthly_periods,
            y: data.monthly_ratios,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Transfer Ratio (%)',
            line: {
                color: '#2196F3',
                width: 3
            },
            marker: {
                color: data.efficiency_levels.map(level => {
                    switch(level) {
                        case 'High Efficiency': return '#4CAF50';
                        case 'Moderate Efficiency': return '#8BC34A';
                        case 'Low Efficiency': return '#FFC107';
                        default: return '#FF9800';
                    }
                }),
                size: 8,
                line: { color: 'white', width: 2 }
            },
            text: data.monthly_periods.map((period, index) => 
                `${period}<br>Transfer Ratio: ${data.monthly_ratios[index].toFixed(1)}%<br>Efficiency: ${data.efficiency_levels[index]}<br>Retail Sales: ${formatCurrency(data.monthly_retail_sales[index])}<br>Retail Transfers: ${formatCurrency(data.monthly_retail_transfers[index])}`
            ),
            hovertemplate: '%{text}<extra></extra>'
        };

        const layout = {
            title: {
                text: `Overall Transfer Ratio: ${data.overall_transfer_ratio.toFixed(1)}% (${data.efficiency_rating}) | Trend: ${data.trend}`,
                font: { size: 14, color: '#333' }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            font: { family: 'Segoe UI, Arial, sans-serif', color: '#333' },
            xaxis: {
                title: { text: 'Month', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                tickangle: -45,
                gridcolor: 'rgba(0,0,0,0.1)'
            },
            yaxis: {
                title: { text: 'Transfer Ratio (%)', font: { size: 14, color: '#666' } },
                tickfont: { color: '#666' },
                gridcolor: 'rgba(0,0,0,0.1)'
            },
            shapes: [
                {
                    type: 'rect',
                    x0: data.monthly_periods[0],
                    x1: data.monthly_periods[data.monthly_periods.length - 1],
                    y0: 15,
                    y1: 25,
                    fillcolor: 'rgba(76, 175, 80, 0.1)',
                    line: { width: 0 }
                }
            ],
            annotations: [
                {
                    text: `High Efficiency Zone (15-25%)<br>Total Activity: ${formatCurrency(data.total_retail_activity)}`,
                    x: data.monthly_periods[Math.floor(data.monthly_periods.length / 2)],
                    y: 30,
                    showarrow: false,
                    font: { size: 11, color: '#4CAF50' },
                    bgcolor: 'rgba(255,255,255,0.9)',
                    bordercolor: '#4CAF50',
                    borderwidth: 1
                }
            ],
            showlegend: false,
            margin: { t: 50, r: 20, b: 80, l: 80 }
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
            x: data.periods,
            y: data.growth_percentages,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Growth Rate (%)',
            line: {
                color: '#2196F3',
                width: 3,
                shape: 'spline'
            },
            marker: {
                color: data.growth_categories.map(category => {
                    switch(category) {
                        case 'Strong Growth': return '#4CAF50';
                        case 'Moderate Growth': return '#8BC34A';
                        case 'Slight Growth': return '#CDDC39';
                        case 'Slight Decline': return '#FFC107';
                        case 'Moderate Decline': return '#FF9800';
                        case 'Strong Decline': return '#F44336';
                        default: return '#9E9E9E';
                    }
                }),
                size: 10,
                line: {
                    color: '#ffffff',
                    width: 2
                }
            },
            text: data.periods.map((period, index) => 
                `${period}<br>Growth: ${data.growth_percentages[index].toFixed(1)}%<br>Category: ${data.growth_categories[index]}<br>Current: ${formatCurrency(data.total_sales[index])}<br>Previous: ${formatCurrency(data.previous_month_sales[index])}<br>Change: ${formatCurrency(data.growth_amounts[index])}`
            ),
            hovertemplate: '%{text}<extra></extra>'
        };

        // Add horizontal reference lines for different growth zones
        const shapes = [
            {
                type: 'line',
                x0: data.periods[0],
                x1: data.periods[data.periods.length - 1],
                y0: 0,
                y1: 0,
                line: {
                    color: 'rgba(0,0,0,0.5)',
                    width: 2,
                    dash: 'dash'
                }
            },
            {
                type: 'line',
                x0: data.periods[0],
                x1: data.periods[data.periods.length - 1],
                y0: 10,
                y1: 10,
                line: {
                    color: 'rgba(76, 175, 80, 0.5)',
                    width: 1,
                    dash: 'dot'
                }
            },
            {
                type: 'line',
                x0: data.periods[0],
                x1: data.periods[data.periods.length - 1],
                y0: -10,
                y1: -10,
                line: {
                    color: 'rgba(244, 67, 54, 0.5)',
                    width: 1,
                    dash: 'dot'
                }
            }
        ];

        const layout = {
            title: {
                text: `Avg Growth: ${data.average_growth_rate.toFixed(1)}% | Latest: ${data.latest_growth_rate.toFixed(1)}% (${data.latest_trend}) | Positive Months: ${data.positive_growth_months}/${data.total_comparison_months}`,
                font: { size: 13, color: '#333' }
            },
            xaxis: {
                title: 'Month',
                gridcolor: 'rgba(0,0,0,0.1)',
                showgrid: true,
                tickangle: -45,
                tickfont: { size: 10 }
            },
            yaxis: {
                title: 'Growth Rate (%)',
                gridcolor: 'rgba(0,0,0,0.1)',
                showgrid: true,
                zeroline: true,
                zerolinecolor: 'rgba(0,0,0,0.5)',
                zerolinewidth: 2
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            shapes: shapes,
            annotations: [
                {
                    x: data.periods[Math.floor(data.periods.length * 0.8)],
                    y: 15,
                    text: 'High Growth Zone (>10%)',
                    showarrow: false,
                    font: { size: 10, color: '#4CAF50' },
                    bgcolor: 'rgba(255,255,255,0.9)',
                    bordercolor: '#4CAF50',
                    borderwidth: 1
                },
                {
                    x: data.periods[Math.floor(data.periods.length * 0.2)],
                    y: -15,
                    text: 'Decline Zone (<-10%)',
                    showarrow: false,
                    font: { size: 10, color: '#F44336' },
                    bgcolor: 'rgba(255,255,255,0.9)',
                    bordercolor: '#F44336',
                    borderwidth: 1
                },
                {
                    x: data.periods[Math.floor(data.periods.length * 0.5)],
                    y: data.average_growth_rate + 5,
                    text: `Trend Direction: ${data.trend_direction}<br>Growth Consistency: ${data.growth_consistency.toFixed(1)}%`,
                    showarrow: true,
                    arrowcolor: data.trend_direction === 'Positive' ? '#4CAF50' : '#F44336',
                    font: { size: 10, color: '#333' },
                    bgcolor: 'rgba(255,255,255,0.9)',
                    bordercolor: data.trend_direction === 'Positive' ? '#4CAF50' : '#F44336',
                    borderwidth: 1
                }
            ],
            showlegend: false,
            margin: { t: 60, r: 20, b: 80, l: 60 }
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

        // Create horizontal bar chart for turnover by item type
        const turnoverTrace = {
            x: data.monthly_avg_movements,
            y: data.item_types,
            type: 'bar',
            orientation: 'h',
            name: 'Monthly Avg Movement',
            marker: {
                color: data.turnover_ratings.map(rating => {
                    switch(rating) {
                        case 'High Turnover': return '#4CAF50';
                        case 'Moderate Turnover': return '#8BC34A';
                        case 'Low Turnover': return '#FFC107';
                        case 'Very Low Turnover': return '#FF9800';
                        default: return '#9E9E9E';
                    }
                }),
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            },
            text: data.monthly_avg_movements.map((movement, index) => 
                `${formatLargeNumber(movement)}/month<br>(${data.turnover_ratings[index]})`
            ),
            textposition: 'outside',
            textfont: { size: 10, color: '#333' },
            hovertemplate: 
                '<b>%{y}</b><br>' +
                'Monthly Avg: %{x:$,.0f}<br>' +
                'Total Movement: %{customdata.total:$,.0f}<br>' +
                'Rating: %{customdata.rating}<br>' +
                'Retail Sales: %{customdata.retail:$,.0f}<br>' +
                'Transfers: %{customdata.transfers:$,.0f}<br>' +
                'Warehouse: %{customdata.warehouse:$,.0f}<br>' +
                '<extra></extra>',
            customdata: data.item_types.map((type, index) => ({
                total: data.total_movements[index],
                rating: data.turnover_ratings[index],
                retail: data.retail_sales[index],
                transfers: data.retail_transfers[index],
                warehouse: data.warehouse_sales[index]
            }))
        };

        const layout = {
            title: {
                text: `Avg Monthly Turnover: ${formatCurrency(data.average_monthly_turnover)} | Top Category: ${data.top_turnover_category} | High Performers: ${data.high_turnover_categories}/${data.total_categories}`,
                font: { size: 13, color: '#333' }
            },
            xaxis: {
                title: 'Average Monthly Movement ($)',
                gridcolor: 'rgba(0,0,0,0.1)',
                showgrid: true,
                tickformat: ',.0f'
            },
            yaxis: {
                title: 'Item Type',
                automargin: true,
                tickfont: { size: 10 }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            annotations: [
                {
                    x: 0.98,
                    y: 0.02,
                    xref: 'paper',
                    yref: 'paper',
                    text: `<b>Turnover Analysis:</b><br>Total Turnover: ${formatCurrency(data.total_turnover)}<br>Analysis Period: ${data.unique_months_analyzed} months<br>Performance Zones:<br>🟢 High (≥50K/month) 🟡 Moderate (20-50K)<br>🟠 Low (5-20K) ⚫ Very Low (<5K)`,
                    showarrow: false,
                    font: { size: 10, color: '#333' },
                    xanchor: 'right',
                    bgcolor: 'rgba(255,255,255,0.95)',
                    bordercolor: '#1976D2',
                    borderwidth: 1,
                    align: 'left'
                }
            ],
            showlegend: false,
            margin: { t: 60, r: 20, b: 50, l: 120 }
        };

        Plotly.newPlot('inventory-turnover-container', [turnoverTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching inventory turnover data:', error);
    });

// Fetch and display Sales per Supplier
fetch('http://127.0.0.1:5000/api/sales_per_supplier')
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error:', data.error);
            return;
        }

        // Take top 15 suppliers for better visibility
        const topSuppliers = data.suppliers.slice(0, 15);
        const topSales = data.total_sales.slice(0, 15);
        const topShares = data.market_shares.slice(0, 15);
        const topTiers = data.partnership_tiers.slice(0, 15);

        // Create horizontal bar chart for top suppliers
        const supplierTrace = {
            x: topSales,
            y: topSuppliers.map((supplier, index) => 
                supplier.length > 25 ? supplier.substring(0, 25) + '...' : supplier
            ),
            type: 'bar',
            orientation: 'h',
            name: 'Total Sales',
            marker: {
                color: topTiers.map(tier => {
                    switch(tier) {
                        case 'Strategic Partner': return '#1976D2';
                        case 'Key Partner': return '#2196F3';
                        case 'Important Partner': return '#4CAF50';
                        case 'Regular Partner': return '#FF9800';
                        case 'Minor Partner': return '#9E9E9E';
                        default: return '#607D8B';
                    }
                }),
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            },
            text: topSales.map((sales, index) => 
                `${formatCurrency(sales)}<br>(${topShares[index].toFixed(1)}%)<br>${topTiers[index]}`
            ),
            textposition: 'outside',
            textfont: { size: 9, color: '#333' },
            hovertemplate: 
                '<b>%{customdata.supplier}</b><br>' +
                'Total Sales: %{x:$,.0f}<br>' +
                'Market Share: %{customdata.share:.1f}%<br>' +
                'Partnership Tier: %{customdata.tier}<br>' +
                'Retail Sales: %{customdata.retail:$,.0f}<br>' +
                'Transfers: %{customdata.transfers:$,.0f}<br>' +
                'Warehouse: %{customdata.warehouse:$,.0f}<br>' +
                '<extra></extra>',
            customdata: topSuppliers.map((supplier, index) => ({
                supplier: supplier,
                share: topShares[index],
                tier: topTiers[index],
                retail: data.retail_sales[index],
                transfers: data.retail_transfers[index],
                warehouse: data.warehouse_sales[index]
            }))
        };

        const layout = {
            title: {
                text: `Top Supplier: ${data.top_supplier} (${data.top_supplier_share.toFixed(1)}%) | Strategic Partners: ${data.strategic_partners_count} | Key Partners: ${data.key_partners_count} | Diversity: ${data.supplier_diversity}`,
                font: { size: 12, color: '#333' }
            },
            xaxis: {
                title: 'Total Sales ($)',
                gridcolor: 'rgba(0,0,0,0.1)',
                showgrid: true,
                tickformat: ',.0f'
            },
            yaxis: {
                title: 'Supplier',
                automargin: true,
                tickfont: { size: 9 }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            annotations: [
                {
                    x: 0.98,
                    y: 0.02,
                    xref: 'paper',
                    yref: 'paper',
                    text: `<b>Partnership Overview:</b><br>Total Suppliers: ${data.total_suppliers}<br>Top 10 Control: ${data.top_10_market_share.toFixed(1)}%<br>Avg per Supplier: ${formatCurrency(data.average_sales_per_supplier)}<br><br><b>Partnership Tiers:</b><br>🔵 Strategic (≥15%) 🟦 Key (8-15%)<br>🟢 Important (3-8%) 🟠 Regular (1-3%)<br>⚫ Minor (<1%)`,
                    showarrow: false,
                    font: { size: 9, color: '#333' },
                    xanchor: 'right',
                    bgcolor: 'rgba(255,255,255,0.95)',
                    bordercolor: '#1976D2',
                    borderwidth: 1,
                    align: 'left'
                }
            ],
            showlegend: false,
            margin: { t: 60, r: 20, b: 50, l: 150 }
        };

        Plotly.newPlot('sales-supplier-container', [supplierTrace], layout, {responsive: true});
    })
    .catch(error => {
        console.error('Error fetching sales per supplier data:', error);
    });



// Fetch and display Top Items by Retail Transfers
function loadTopItemsByTransfers() {
    console.log('Starting to fetch Top Items by Retail Transfers...');
    fetch('http://127.0.0.1:5000/api/top_items_by_transfers')
        .then(response => response.json())
        .then(data => {
            console.log('Received transfers data:', data);
            if (data.error) {
                console.error('Error:', data.error);
                return;
            }

        // Create horizontal bar chart for top items by retail transfers
        const transfersTrace = {
            x: data.retail_transfers,
            y: data.display_labels,
            type: 'bar',
            orientation: 'h',
            name: 'Retail Transfers',
            marker: {
                color: data.logistics_performances.map(performance => {
                    switch(performance) {
                        case 'High Transfer Focus': return '#1976D2';
                        case 'Moderate Transfer Focus': return '#2196F3';
                        case 'Balanced Distribution': return '#4CAF50';
                        case 'Sales Focus': return '#FF9800';
                        case 'Minimal Transfers': return '#9E9E9E';
                        default: return '#607D8B';
                    }
                }),
                line: {
                    color: 'rgba(255,255,255,0.8)',
                    width: 1
                }
            },
            text: data.retail_transfers.map((transfers, index) => 
                `${transfers.toLocaleString()}<br>(${data.transfer_efficiencies[index].toFixed(1)}%)<br>${data.logistics_performances[index]}`
            ),
            textposition: 'outside',
            textfont: { size: 9, color: '#333' },
            hovertemplate: 
                '<b>%{customdata.description}</b><br>' +
                'Item Code: %{customdata.code}<br>' +
                'Item Type: %{customdata.type}<br>' +
                'Transfers: %{x:,.0f}<br>' +
                'Transfer Efficiency: %{customdata.efficiency:.1f}%<br>' +
                'Logistics Performance: %{customdata.performance}<br>' +
                'Retail Sales: %{customdata.sales:$,.0f}<br>' +
                '<extra></extra>',
            customdata: data.item_codes.map((code, index) => ({
                code: code,
                description: data.item_descriptions[index],
                type: data.item_types[index],
                efficiency: data.transfer_efficiencies[index],
                performance: data.logistics_performances[index],
                sales: data.retail_sales[index]
            }))
        };

        const layout = {
            title: {
                text: `Top Transfer Item: ${data.top_transfer_item} (${data.top_transfer_amount.toLocaleString()}) | Top 15 Account for ${data.top_15_percentage.toFixed(1)}% | Transfer-Focused: ${data.transfer_focused_items}/15`,
                font: { size: 12, color: '#333' }
            },
            xaxis: {
                title: 'Number of Retail Transfers',
                gridcolor: 'rgba(0,0,0,0.1)',
                showgrid: true,
                tickformat: ',.0f'
            },
            yaxis: {
                title: 'Item (Code - Description)',
                automargin: true,
                tickfont: { size: 9 }
            },
            plot_bgcolor: 'rgba(0,0,0,0)',
            paper_bgcolor: 'rgba(0,0,0,0)',
            annotations: [
                {
                    x: 0.98,
                    y: 0.02,
                    xref: 'paper',
                    yref: 'paper',
                    text: `<b>Logistics Analytics:</b><br>Total Transfer Items: ${data.total_transfer_items}<br>Dominant Type: ${data.dominant_transfer_type}<br>Total Transfers: ${data.total_retail_transfers.toLocaleString()}<br><br><b>Performance Categories:</b><br>🔵 High Focus (≥50% efficiency)<br>🟦 Moderate Focus (30-50%)<br>🟢 Balanced (15-30%)<br>🟠 Sales Focus (5-15%)<br>⚫ Minimal (<5%)`,
                    showarrow: false,
                    font: { size: 9, color: '#333' },
                    xanchor: 'right',
                    bgcolor: 'rgba(255,255,255,0.95)',
                    bordercolor: '#1976D2',
                    borderwidth: 1,
                    align: 'left'
                }
            ],
            showlegend: false,
            margin: { t: 60, r: 20, b: 50, l: 200 }
        };

        Plotly.newPlot('retail-transfers-container', [transfersTrace], layout, {responsive: true});
        })
        .catch(error => {
            console.error('Error fetching top items by transfers data:', error);
            // Add visible error message to the container
            const container = document.getElementById('retail-transfers-container');
            if (container) {
                container.innerHTML = '<p style="color:red;padding:20px;">Error loading Top Items by Retail Transfers: ' + error.message + '</p>';
            }
        });
}

// Call the function with a delay to ensure DOM is ready
setTimeout(loadTopItemsByTransfers, 2000);

// Fetch and display Sales Seasonality
function loadSalesSeasonality() {
    console.log('Starting to fetch Sales Seasonality...');
    fetch('http://127.0.0.1:5000/api/sales_seasonality')
        .then(response => response.json())
        .then(data => {
            console.log('Received seasonality data:', data);
            if (data.error) {
                console.error('Error:', data.error);
                const container = document.getElementById('sales-seasonality-container');
                if (container) {
                    container.innerHTML = '<p style="color:red;padding:20px;">Error loading Sales Seasonality: ' + data.error + '</p>';
                }
                return;
            }

            // Create stacked area chart for sales seasonality
            const retailTrace = {
                x: data.periods,
                y: data.retail_sales,
                name: 'Retail Sales',
                type: 'scatter',
                mode: 'lines',
                stackgroup: 'sales',
                fill: 'tonexty',
                fillcolor: 'rgba(33, 150, 243, 0.7)',
                line: {
                    color: '#2196F3',
                    width: 2
                },
                hovertemplate: 
                    '<b>%{x}</b><br>' +
                    'Retail Sales: %{y:$,.0f}<br>' +
                    'Contribution: %{customdata:.1f}%<br>' +
                    '<extra></extra>',
                customdata: data.periods.map((_, index) => 
                    (data.retail_sales[index] / data.total_sales[index]) * 100
                )
            };

            const transfersTrace = {
                x: data.periods,
                y: data.retail_transfers,
                name: 'Retail Transfers',
                type: 'scatter',
                mode: 'lines',
                stackgroup: 'sales',
                fill: 'tonexty',
                fillcolor: 'rgba(255, 152, 0, 0.7)',
                line: {
                    color: '#FF9800',
                    width: 2
                },
                hovertemplate: 
                    '<b>%{x}</b><br>' +
                    'Retail Transfers: %{y:$,.0f}<br>' +
                    'Contribution: %{customdata:.1f}%<br>' +
                    '<extra></extra>',
                customdata: data.periods.map((_, index) => 
                    (data.retail_transfers[index] / data.total_sales[index]) * 100
                )
            };

            const warehouseTrace = {
                x: data.periods,
                y: data.warehouse_sales,
                name: 'Warehouse Sales',
                type: 'scatter',
                mode: 'lines',
                stackgroup: 'sales',
                fill: 'tonexty',
                fillcolor: 'rgba(76, 175, 80, 0.7)',
                line: {
                    color: '#4CAF50',
                    width: 2
                },
                hovertemplate: 
                    '<b>%{x}</b><br>' +
                    'Warehouse Sales: %{y:$,.0f}<br>' +
                    'Contribution: %{customdata:.1f}%<br>' +
                    '<extra></extra>',
                customdata: data.periods.map((_, index) => 
                    (data.warehouse_sales[index] / data.total_sales[index]) * 100
                )
            };

            // Add total sales line trace
            const totalTrace = {
                x: data.periods,
                y: data.total_sales,
                name: 'Total Sales',
                type: 'scatter',
                mode: 'lines+markers',
                line: {
                    color: '#1976D2',
                    width: 3,
                    dash: 'dot'
                },
                marker: {
                    color: '#1976D2',
                    size: 8,
                    line: {
                        color: '#ffffff',
                        width: 2
                    }
                },
                hovertemplate: 
                    '<b>%{x}</b><br>' +
                    'Total Sales: %{y:$,.0f}<br>' +
                    'Seasonality Index: %{customdata:.1f}<br>' +
                    '<extra></extra>',
                customdata: data.periods.map((_, index) => 
                    (data.total_sales[index] / data.average_monthly_sales) * 100
                ),
                yaxis: 'y2'
            };

            const layout = {
                title: {
                    text: `Peak: ${data.peak_month} ($${data.peak_value.toLocaleString()}) | Valley: ${data.valley_month} ($${data.valley_value.toLocaleString()}) | Current Trend: ${data.trend} | YoY Growth: ${data.year_over_year_growth.toFixed(1)}%`,
                    font: { size: 12, color: '#333' }
                },
                xaxis: {
                    title: 'Time Period (Month-Year)',
                    gridcolor: 'rgba(0,0,0,0.1)',
                    showgrid: true,
                    tickangle: -45
                },
                yaxis: {
                    title: 'Sales Amount ($)',
                    gridcolor: 'rgba(0,0,0,0.1)',
                    showgrid: true,
                    tickformat: '$,.0f',
                    side: 'left'
                },
                yaxis2: {
                    title: 'Total Sales Trend ($)',
                    overlaying: 'y',
                    side: 'right',
                    tickformat: '$,.0f',
                    showgrid: false
                },
                plot_bgcolor: 'rgba(0,0,0,0)',
                paper_bgcolor: 'rgba(0,0,0,0)',
                hovermode: 'x unified',
                annotations: [
                    {
                        x: 0.02,
                        y: 0.98,
                        xref: 'paper',
                        yref: 'paper',
                        text: `<b>Seasonality Analysis:</b><br>Current Performance: ${data.seasonal_performance}<br>Seasonality Index: ${data.seasonality_index.toFixed(1)}<br>Months Analyzed: ${data.months_analyzed}<br><br><b>Channel Contributions:</b><br>🔵 Retail: ${data.retail_contribution.toFixed(1)}%<br>🟠 Transfers: ${data.transfers_contribution.toFixed(1)}%<br>🟢 Warehouse: ${data.warehouse_contribution.toFixed(1)}%<br><br><b>Trend Indicators:</b><br>📈 Peak Season: ${data.peak_month}<br>📉 Valley Season: ${data.valley_month}<br>📊 Average Monthly: $${data.average_monthly_sales.toLocaleString()}`,
                        showarrow: false,
                        font: { size: 9, color: '#333' },
                        xanchor: 'left',
                        yanchor: 'top',
                        bgcolor: 'rgba(255,255,255,0.95)',
                        bordercolor: '#1976D2',
                        borderwidth: 1,
                        align: 'left'
                    }
                ],
                showlegend: true,
                legend: {
                    orientation: 'h',
                    x: 0.5,
                    xanchor: 'center',
                    y: -0.2
                },
                margin: { t: 80, r: 60, b: 120, l: 80 }
            };

            Plotly.newPlot('sales-seasonality-container', [retailTrace, transfersTrace, warehouseTrace, totalTrace], layout, {responsive: true});
        })
        .catch(error => {
            console.error('Error fetching sales seasonality data:', error);
            const container = document.getElementById('sales-seasonality-container');
            if (container) {
                container.innerHTML = '<p style="color:red;padding:20px;">Error loading Sales Seasonality: ' + error.message + '</p>';
            }
        });
}

// Call the function with a delay to ensure DOM is ready
setTimeout(loadSalesSeasonality, 3000);
