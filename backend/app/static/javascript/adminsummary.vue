<template>
    <div>
        <h1>Admin Summary Dashboard</h1>
        <div class="chart-container">
            <canvas id="adminCustomerChart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="adminProfessionalChart"></canvas>
        </div>
        <div class="chart-container">
            <canvas id="adminServiceRequestChart"></canvas>
        </div>
    </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import Chart from 'chart.js/auto';

export default {
    props: {
        flaggedCount: {
            type: Number,
            required: true
        },
        notFlaggedCount: {
            type: Number,
            required: true
        },
        professionalNames: {
            type: Array,
            required: true
        },
        professionalRatings: {
            type: Array,
            required: true
        },
        requestCategories: {
            type: Array,
            required: true
        },
        requestRatings: {
            type: Array,
            required: true
        }
    },
    setup(props) {
        onMounted(() => {
            // Chart 1: Customer Flagged Status
            const ctxAdminCustomers = document.getElementById('adminCustomerChart');
            new Chart(ctxAdminCustomers, {
                type: 'bar',
                data: {
                    labels: ['Flagged', 'Not Flagged'],
                    datasets: [{
                        label: 'Customers',
                        data: [props.flaggedCount, props.notFlaggedCount],
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.5)',
                            'rgba(54, 162, 235, 0.5)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    title: {
                        display: true,
                        text: 'Customer Flagged Status'
                    },
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                }
            });

            // Chart 2: Professional Ratings
            const ctxAdminProfessionals = document.getElementById('adminProfessionalChart');
            new Chart(ctxAdminProfessionals, {
                type: 'bar',
                data: {
                    labels: props.professionalNames,
                    datasets: [{
                        label: 'Ratings',
                        data: props.professionalRatings,
                        backgroundColor: 'rgba(75, 192, 192, 0.5)'
                    }]
                },
                options: {
                    responsive: true,
                    title: {
                        display: true,
                        text: 'Professional Ratings'
                    },
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                }
            });

            // Chart 3: Service Request Status
            const ctxAdminServiceRequests = document.getElementById('adminServiceRequestChart');
            new Chart(ctxAdminServiceRequests, {
                type: 'bar',
                data: {
                    labels: props.requestCategories,
                    datasets: [{
                        label: 'Number of Requests',
                        data: props.requestRatings,
                        backgroundColor: 'rgba(153, 102, 255, 0.5)'
                    }]
                },
                options: {
                    responsive: true,
                    title: {
                        display: true,
                        text: 'Service Request Status'
                    },
                    barPercentage: 0.7,
                    categoryPercentage: 0.8
                }
            });
        });

        return {};
    }
};
</script>

<style>
canvas {
    -moz-user-select: none;
    -webkit-user-select: none;
    -ms-user-select: none;
    user-select: none;
}

.chart-container {
    width: 50%;
    margin: auto;
}
</style>