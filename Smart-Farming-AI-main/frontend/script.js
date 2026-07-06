async function loadData() {
  const res = await fetch("http://127.0.0.1:5000/api/irrigation");
  const data = await res.json();

  document.getElementById("moistureValue").innerText =
    `${data.moisture}`;

  document.getElementById("tempValue").innerText =
    `${data.temperature} °C`;

  document.getElementById("fieldStatus").innerText =
    `Field Status: ${data.moisture < 300 ? "VERY WET" : "CHECK"}`;

  document.getElementById("pumpDecision").innerText =
    `Pump: ${data.pump}`;

  document.getElementById("duration").innerText =
    `Duration: ${data.duration}`;

  document.getElementById("justification").innerText =
    data.justification;
}
