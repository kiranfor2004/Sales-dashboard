// Operational Dashboard JavaScript - 6 KPIs

const API_BASE = 'http://127.0.0.1:5000/api';

// Chart configuration
const chartConfig = {
    responsive: true,
    displayModeBar: false,
    layout: {
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Segoe UI, Arial, sans-serif', size: 12 },
        margin: { l: 60, r: 20, t: 30, b: 80 },
        showlegend: true,
        legend: {
            orientation: 'h',
            x: 0.5,
            xanchor: 'center',
            y: -0.15,
            font: { size: 11 }
        }
    }
};

// Utility function to create charts
async function createChart(endpoint, chartId, chartFunction) {
    try {
        const response = await fetch(`${API_BASE}/${endpoint}`);
        const data = await response.json();
        
        if (data.error) {
            document.getElementById(chartId).innerHTML = `<div class="error">Error: ${data.error}</div>`;
            return;
        }
        
        chartFunction(data, chartId);
    } catch (error) {
        console.error(`Error loading ${chartId}:`, error);
        document.getElementById(chartId).innerHTML = `<div class="error">Failed to load chart</div>`;
    }
}

// 1. Overall Sales Performance Chart
function createOverallSalesPerformance(data, chartId) {
    const trace = {
        x: data.revenue_streams,
        y: data.total_amounts,
        type: 'bar',
        marker: { 
            color: ['#3498db', '#e74c3c', '#2ecc71'],
            line: {
                color: '#2c3e50',
                width: 1
            }
        },
        text: data.total_amounts.map(val => `$${val.toLocaleString()}`),
        textposition: 'outside',
        name: 'Sales Performance'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Overall Sales Performance', font: { size: 16, color: '#2c3e50' } },
        xaxis: { title: 'Revenue Stream', gridcolor: '#ecf0f1' },
        yaxis: { 
            title: 'Sales Value ($)', 
            gridcolor: '#ecf0f1',
            tickformat: '$,.0f'
        },
        height: 450
    };

    Plotly.newPlot(chartId, [trace], layout, chartConfig);
}

// 2. Month-over-Month Sales Growth Chart
function createMonthOverMonthGrowth(data, chartId) {
    const growthRates = data.growth_percentages || [];
    const periods = data.periods || [];
    const colors = growthRates.map(rate => rate >= 0 ? '#27ae60' : '#e74c3c');

    const trace = {
        x: periods,
        y: growthRates,
        type: 'bar',
        marker: { color: colors },
        name: 'Growth Rate %'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Monthly Growth Performance', font: { size: 16, color: '#2c3e50' } },
        xaxis: { title: 'Month', gridcolor: '#ecf0f1' },
        yaxis: { title: 'Growth Rate (%)', gridcolor: '#ecf0f1' }
    };

    Plotly.newPlot(chartId, [trace], layout, chartConfig);
}

// 3. Sales Transfer Ratio Chart
function createSalesTransferRatio(data, chartId) {
    const trace = {
        x: data.monthly_periods || [],
        y: data.monthly_ratios || [],
        type: 'scatter',
        mode: 'lines+markers',
        fill: 'tozeroy',
        line: { color: '#3498db', width: 3 },
        marker: { color: '#2980b9', size: 8 },
        name: 'Transfer Ratio %'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Monthly Transfer Efficiency', font: { size: 16, color: '#2c3e50' } },
        xaxis: { title: 'Month', gridcolor: '#ecf0f1' },
        yaxis: { title: 'Ratio (%)', gridcolor: '#ecf0f1' }
    };

    Plotly.newPlot(chartId, [trace], layout, chartConfig);
}

// 4. Inventory Turnover Rate Chart
function createInventoryTurnover(data, chartId) {
    const trace = {
        x: data.monthly_periods || [],
        y: data.monthly_turnovers || [],
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#e67e22', width: 3 },
        marker: { color: '#d35400', size: 8 },
        name: 'Turnover Rate'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Monthly Inventory Efficiency', font: { size: 16, color: '#2c3e50' } },
        xaxis: { title: 'Month', gridcolor: '#ecf0f1' },
        yaxis: { title: 'Turnover Rate', gridcolor: '#ecf0f1' }
    };

    Plotly.newPlot(chartId, [trace], layout, chartConfig);
}

// 5. Top Items by Retail Transfers Chart
function createTopItemsByRetailTransfers(data, chartId) {
    // Limit to top 10 for better readability
    const topItems = 10;
    const labels = data.display_labels.slice(0, topItems) || [];
    const transferValues = data.retail_transfers.slice(0, topItems) || [];
    
    const trace = {
        x: labels,
        y: transferValues,
        type: 'bar',
        marker: { 
            color: '#9b59b6',
            colorscale: 'Viridis'
        },
        name: 'Transfer Value',
        text: transferValues.map(val => `$${val.toLocaleString()}`),
        textposition: 'outside'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Top 10 Items by Retail Transfers', font: { size: 16, color: '#2c3e50' } },
        xaxis: { 
            title: 'Items', 
            gridcolor: '#ecf0f1',
            tickangle: -45
        },
        yaxis: { 
            title: 'Transfer Value ($)', 
            gridcolor: '#ecf0f1',
            tickformat: '$,.0f'
        },
        height: 500,
        margin: { l: 80, r: 50, t: 50, b: 120 }
    };

    Plotly.newPlot(chartId, [trace], layout, chartConfig);
}

// 6. Top Selling Items Chart
function createTopSellingItems(data, chartId) {
    // Use the correct field names and limit to top 10
    const labels = data.display_labels.slice(0, 10);
    const salesValues = data.retail_sales.slice(0, 10);
    
    const trace = {
        x: labels,
        y: salesValues,
        type: 'bar',
        marker: { 
            color: '#16a085',
            line: {
                color: '#138D75',
                width: 1
            }
        },
        text: salesValues.map(val => `$${val.toLocaleString()}`),
        textposition: 'outside',
        name: 'Sales Value'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Top 10 Best Performing Products', font: { size: 16, color: '#2c3e50' } },
        xaxis: { 
            title: 'Products', 
            gridcolor: '#ecf0f1',
            tickangle: -45
        },
        yaxis: { 
            title: 'Sales Value ($)', 
            gridcolor: '#ecf0f1',
            tickformat: '$,.0f'
        },
        height: 500,
        margin: { l: 80, r: 50, t: 50, b: 120 }
    };

    Plotly.newPlot(chartId, [trace], layout, chartConfig);
}

// Initialize all charts when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Load all operational KPIs using existing endpoints
    createChart('overall_sales_performance', 'overallSalesPerformance', createOverallSalesPerformance);
    createChart('month_over_month_growth', 'monthOverMonthGrowth', createMonthOverMonthGrowth);
    createChart('sales_transfer_ratio', 'salesTransferRatio', createSalesTransferRatio);
    createChart('inventory_turnover_rate', 'inventoryTurnover', createInventoryTurnover);
    createChart('top_items_by_transfers', 'topItemsByRetailTransfers', createTopItemsByRetailTransfers);
    createChart('top_selling_items', 'topSellingItems', createTopSellingItems);
});

// Add loading indicators
function showLoading(chartId) {
    document.getElementById(chartId).innerHTML = '<div class="loading">Loading chart data...</div>';
}

// Add error styling
const style = document.createElement('style');
style.textContent = `
    .loading {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 300px;
        color: #7f8c8d;
        font-size: 16px;
    }
    
    .error {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 300px;
        color: #e74c3c;
        font-size: 16px;
        background: rgba(231, 76, 60, 0.1);
        border-radius: 5px;
        margin: 1rem;
    }
`;
document.head.appendChild(style);
