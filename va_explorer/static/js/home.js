GRAPH_OPTIONS = {
  responsive: true,
  scales: { y: { beginAtZero: true } },
  plugins: { legend: { display: false } }
};

BORDER_COLOR = "#037BFE"

const setVATrendsTableData = (vaTableData) => {
  document.getElementById('interviewed-past-24-hours').innerHTML = vaTableData.collected["24"];
  document.getElementById('interviewed-past-week').innerHTML = vaTableData.collected["1 week"];
  document.getElementById('interviewed-past-month').innerHTML =  vaTableData.collected["1 month"];
  document.getElementById('interviewed-overall').innerHTML = vaTableData.collected["Overall"];

  document.getElementById('coded-past-24-hours').innerHTML = vaTableData.coded["24"];
  document.getElementById('coded-past-week').innerHTML = vaTableData.coded["1 week"];
  document.getElementById('coded-past-month').innerHTML =  vaTableData.coded["1 month"];
  document.getElementById('coded-overall').innerHTML = vaTableData.coded["Overall"];

  document.getElementById('uncoded-past-24-hours').innerHTML = vaTableData.uncoded["24"];
  document.getElementById('uncoded-past-week').innerHTML = vaTableData.uncoded["1 week"];
  document.getElementById('uncoded-past-month').innerHTML =  vaTableData.uncoded["1 month"];
  document.getElementById('uncoded-overall').innerHTML = vaTableData.uncoded["Overall"];
}

const setVARow = (root, row, isFieldWorker) => {
  if(isFieldWorker) {
    root.insertAdjacentHTML('beforebegin',
`<tr>
        <td>${row.id}</td>
        <td>${row.interviewed}</td>
        <td>${row.facility}</td>
        <td>${row.deceased}</td>
        <td>${row.dod}</td>
        <td>${row.cause}</td>
        <td>${row.warnings}</td>
        <td>${row.errors}</td>
        <td><a class="btn btn-primary" href="va_data_management/show/${row.id}">View</a></td>
      </tr>`
    )
  }
  else {
    root.insertAdjacentHTML('beforebegin',
`<tr>
        <td>${row.id}</td>
        <td>${row.interviewed}</td>
        <td>${row.interviewer}</td>
        <td>${row.facility}</td>
        <td>${row.deceased}</td>
        <td>${row.dod}</td>
        <td>${row.cause}</td>
        <td>${row.warnings}</td>
        <td>${row.errors}</td>
        <td><a class="btn btn-primary" href="va_data_management/show/${row.id}">View</a></td>
      </tr>`
    )
  }
}

const setCodingIssuesTableData = (codingIssuesData, isFieldWorker) => {
  const root = document.getElementById('coding-issues-root');
  codingIssuesData.forEach(row => setVARow(root, row, isFieldWorker));
}

const setIndeterminateCODTableData = (codingIssuesData, isFieldWorker) => {
  const root = document.getElementById('indeterminate-cod-root');
  codingIssuesData.forEach(row => setVARow(root, row, isFieldWorker));
}

const setVAChart = (x, y, ctx) => {
  new Chart(ctx, {
    type: "line",
    data: {
      labels: x,
      datasets: [{
        data: y,
        borderColor: BORDER_COLOR,
      }]
    },
    options: GRAPH_OPTIONS,
  });
}

const setVACharts = (graphData) => {
  const interviewedCtx = document.getElementById("interviewedChart").getContext("2d");
  const codedCtx = document.getElementById("codedChart").getContext("2d");
  const notYetCodedCtx = document.getElementById("notYetCodedChart").getContext("2d");

  setVAChart(graphData.collected.x, graphData.collected.y, interviewedCtx);
  setVAChart(graphData.coded.x, graphData.coded.y,codedCtx);
  setVAChart(graphData.uncoded.x, graphData.uncoded.y, notYetCodedCtx);
}

const loadAllData = () => {
  const endpoint = "/trends";
  $.ajax({
    url: endpoint,
    type: "GET",
    dataType: "json",
    success: (jsonResponse) => {
      // Set VA Table data
      setVATrendsTableData(jsonResponse.vaTable);
      // Set VA Charts
      setVACharts(jsonResponse.graphs);
      // Set Coding Issues Table data
      if(jsonResponse.issueList.length > 0) {
        setCodingIssuesTableData(jsonResponse.issueList, jsonResponse.isFieldWorker);
        $('#coding-issues').removeClass('hidden');

        if(jsonResponse.additionalIssues > 0) {
          document.getElementById('additional-issues-count').innerHTML =
              jsonResponse.additionalIssues;
          $('#additional-issues-msg').removeClass('hidden');
        }
      }
      else {
        $('#no-coding-issues').removeClass('hidden');
      }
      // Set Indeterminate COD data
      if(jsonResponse.indeterminateCodList.length > 0) {
        setIndeterminateCODTableData(jsonResponse.indeterminateCodList, jsonResponse.isFieldWorker);
        $('#indeterminate-cod').removeClass('hidden');

        if(jsonResponse.additionalIndeterminateCods > 0){
          document.getElementById('additional-indeterminate-cods-count').innerHTML =
              jsonResponse.additionalIndeterminateCods;
          $('#additional-indeterminate-cods-msg').removeClass('hidden');
        }
      }
      else {
        $('#no-indeterminate-cod').removeClass('hidden');
      }
    },
    error: () => console.log("Failed to fetch chart data from " + endpoint + "!")
  });
}

loadAllData();
