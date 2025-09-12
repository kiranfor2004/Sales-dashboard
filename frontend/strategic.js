// Strategic Analytics Dashboard JavaScript - 5 KPIs

const API_BASE = 'http://127.0.0.1:5000/api';

// Chart configuration
const chartConfig = {
    responsive: true,
    displayModeBar: false,
    layout: {
        plot_bgcolor: 'rgba(0,0,0,0)',
        paper_bgcolor: 'rgba(0,0,0,0)',
        font: { family: 'Segoe UI, Arial, sans-serif', size: 12 },
        margin: { l: 60, r: 20, t: 40, b: 60 },
        showlegend: false  // Will be overridden per chart as needed
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

// 1. Sales per Supplier Chart
function createSalesPerSupplier(data, chartId) {
    // Use the correct field names from the API
    const suppliers = data.suppliers.slice(0, 10); // Top 10 suppliers
    const salesValues = data.total_sales.slice(0, 10); // Top 10 sales values
    
    const trace = {
        x: suppliers,
        y: salesValues,
        type: 'bar',
        marker: { 
            color: '#2c3e50',
            line: {
                color: '#34495e',
                width: 1
            }
        },
        name: 'Sales Value',
        text: salesValues.map(val => `$${val.toLocaleString()}`),
        textposition: 'outside'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Top 10 Supplier Performance', font: { size: 16, color: '#2c3e50' } },
        xaxis: { 
            title: 'Suppliers', 
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

// 2. Sales Seasonality Chart
function createSalesSeasonality(data, chartId) {
    const trace1 = {
        x: data.periods,
        y: data.retail_sales,
        type: 'scatter',
        mode: 'lines+markers',
        fill: 'tonexty',
        name: 'Retail Sales',
        line: { width: 3, color: '#3498db' },
        marker: { size: 8 }
    };
    
    const trace2 = {
        x: data.periods,
        y: data.warehouse_sales,
        type: 'scatter',
        mode: 'lines+markers',
        fill: 'tozeroy',
        name: 'Warehouse Sales',
        line: { width: 3, color: '#e74c3c' },
        marker: { size: 8 }
    };
    
    const trace3 = {
        x: data.periods,
        y: data.retail_transfers,
        type: 'scatter',
        mode: 'lines+markers',
        name: 'Retail Transfers',
        line: { width: 2, color: '#2ecc71' },
        marker: { size: 6 }
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Sales Seasonality Patterns', font: { size: 16, color: '#2c3e50' } },
        xaxis: { title: 'Time Period', gridcolor: '#ecf0f1' },
        yaxis: { 
            title: 'Sales Value ($)', 
            gridcolor: '#ecf0f1',
            tickformat: '$,.0f'
        },
        legend: {
            orientation: 'h',
            x: 0.5,
            xanchor: 'center',
            y: -0.12,
            font: { size: 10 }
        },
        height: 420,
        margin: { l: 60, r: 20, t: 40, b: 100 }
    };

    Plotly.newPlot(chartId, [trace1, trace2, trace3], layout, chartConfig);
}

// 3. Sales Mix Chart
function createSalesMix(data, chartId) {
    const trace = {
        labels: data.item_types || [],
        values: data.retail_sales || [],
        type: 'pie',
        marker: { colors: ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6'] },
        textinfo: 'label+percent',
        textposition: 'outside'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Sales Distribution by Category', font: { size: 16, color: '#2c3e50' } },
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.05,
            xanchor: 'left',
            y: 0.5,
            yanchor: 'middle',
            font: { size: 11 }
        },
        height: 400,
        margin: { l: 40, r: 120, t: 40, b: 40 }
    };

    Plotly.newPlot(chartId, [trace], layout, chartConfig);
}

// 4. Sales by Item Type Chart
function createSalesByItemType(data, chartId) {
    const trace = {
        labels: data.item_types || [],
        values: data.retail_sales || [],
        type: 'pie',
        marker: { colors: ['#1abc9c', '#3498db', '#9b59b6', '#e67e22', '#e74c3c'] },
        textinfo: 'label+percent',
        textposition: 'outside'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Item Type Performance Distribution', font: { size: 16, color: '#2c3e50' } },
        showlegend: true,
        legend: {
            orientation: 'v',
            x: 1.05,
            xanchor: 'left',
            y: 0.5,
            yanchor: 'middle',
            font: { size: 11 }
        },
        height: 400,
        margin: { l: 40, r: 120, t: 40, b: 40 }
    };

    Plotly.newPlot(chartId, [trace], layout, chartConfig);
}

// 5. KPI Data Chart (Monthly Comparison)
function createKpiData(data, chartId) {
    const trace1 = {
        x: data.labels,
        y: data.current_month.values,
        type: 'bar',
        name: data.current_month.name,
        marker: { color: '#3498db' },
        text: data.current_month.values.map(val => `$${val.toLocaleString()}`),
        textposition: 'outside'
    };
    
    const trace2 = {
        x: data.labels,
        y: data.previous_month.values,
        type: 'bar',
        name: data.previous_month.name,
        marker: { color: '#e74c3c' },
        text: data.previous_month.values.map(val => `$${val.toLocaleString()}`),
        textposition: 'outside'
    };

    const layout = {
        ...chartConfig.layout,
        title: { text: 'Monthly Performance Comparison', font: { size: 16, color: '#2c3e50' } },
        xaxis: { title: 'Sales Category', gridcolor: '#ecf0f1' },
        yaxis: { 
            title: 'Sales Value ($)', 
            gridcolor: '#ecf0f1',
            tickformat: '$,.0f'
        },
        barmode: 'group',
        legend: {
            orientation: 'h',
            x: 0.5,
            xanchor: 'center',
            y: 1.05,
            font: { size: 10 }
        },
        height: 420,
        margin: { l: 60, r: 20, t: 60, b: 60 }
    };

    Plotly.newPlot(chartId, [trace1, trace2], layout, chartConfig);
}

// Initialize all charts when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Load all strategic KPIs using existing endpoints
    createChart('sales_per_supplier', 'salesPerSupplier', createSalesPerSupplier);
    createChart('sales_seasonality', 'salesSeasonality', createSalesSeasonality);
    createChart('sales_mix', 'salesMix', createSalesMix);
    createChart('sales_by_item_type', 'salesByItemType', createSalesByItemType);
    createChart('kpi_data', 'kpiData', createKpiData);
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
