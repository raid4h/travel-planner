(function () {
  const dataScript = document.getElementById("dashboard-chart-data");
  const root = document.getElementById("dashboard-root");
  if (!dataScript || typeof Chart === "undefined") return;

  let initialData = {};
  try {
    initialData = JSON.parse(dataScript.textContent);
  } catch (e) {
    return;
  }

  const barCanvas = document.getElementById("tripBudgetBarChart");
  const barEmpty = document.getElementById("bar-chart-empty");
  const doughnutCanvas = document.getElementById("categoryDoughnutChart");
  const doughnutEmpty = document.getElementById("doughnut-chart-empty");
  const tripFilter = document.getElementById("chart-trip-filter");

  let barChart = null;
  let doughnutChart = null;

  function renderBarChart(tripChart) {
    if (!barCanvas) return;
    if (!tripChart || !tripChart.has_data) {
      barCanvas.classList.add("hidden");
      if (barEmpty) barEmpty.classList.remove("hidden");
      return;
    }
    barCanvas.classList.remove("hidden");
    if (barEmpty) barEmpty.classList.add("hidden");

    if (barChart) {
      barChart.destroy();
    }
    barChart = new Chart(barCanvas, {
      type: "bar",
      data: {
        labels: tripChart.labels,
        datasets: [
          {
            label: "Planned Budget",
            data: tripChart.budgets,
            backgroundColor: "#93c5fd",
            borderRadius: 6,
          },
          {
            label: "Actual Spent",
            data: tripChart.spent,
            backgroundColor: "#2563eb",
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "bottom" },
        },
        scales: {
          y: { beginAtZero: true },
        },
      },
    });
  }

  function renderDoughnutChart(catChart) {
    if (!doughnutCanvas) return;
    if (!catChart || !catChart.has_data) {
      doughnutCanvas.classList.add("hidden");
      if (doughnutEmpty) doughnutEmpty.classList.remove("hidden");
      return;
    }
    doughnutCanvas.classList.remove("hidden");
    if (doughnutEmpty) doughnutEmpty.classList.add("hidden");

    if (doughnutChart) {
      doughnutChart.data.labels = catChart.labels;
      doughnutChart.data.datasets[0].data = catChart.values;
      doughnutChart.data.datasets[0].backgroundColor = catChart.colors;
      doughnutChart.update();
      return;
    }

    doughnutChart = new Chart(doughnutCanvas, {
      type: "doughnut",
      data: {
        labels: catChart.labels,
        datasets: [
          {
            data: catChart.values,
            backgroundColor: catChart.colors,
            borderWidth: 2,
            borderColor: "#ffffff",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "62%",
        plugins: {
          legend: { position: "right" },
        },
      },
    });
  }

  renderBarChart(initialData.trip_budget_chart);
  renderDoughnutChart(initialData.category_chart);

  if (tripFilter && root && root.dataset.statsUrl) {
    tripFilter.addEventListener("change", async function () {
      const selectedTrip = tripFilter.value;
      const url = selectedTrip
        ? `${root.dataset.statsUrl}?trip=${encodeURIComponent(selectedTrip)}`
        : root.dataset.statsUrl;
      try {
        const resp = await fetch(url);
        if (!resp.ok) return;
        const payload = await resp.json();
        if (payload.charts && payload.charts.category_chart) {
          if (doughnutChart && !payload.charts.category_chart.has_data) {
            doughnutChart.destroy();
            doughnutChart = null;
          }
          renderDoughnutChart(payload.charts.category_chart);
        }
      } catch (e) {
        // Ignore transient network errors on filter switch
      }
    });
  }
})();

