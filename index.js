const express = require("express");
const axios = require("axios");
const cheerio = require("cheerio");

const app = express();
const PORT = process.env.PORT || 5000;

const DEVELOPER_INFO = {
  github: "https://www.github.com/Sudhirxd",
  instagram: "https://www.instagram.com/sudhirxd.in",
  name: "Sudhirxd",
  telegram: "https://t.me/Sudhirxd",
  website: "https://www.sudhirxd.in"
};

const DESIRED_ORDER = [
  "Owner Name",
  "Father's Name",
  "Owner Serial No",
  "Model Name",
  "Maker Model",
  "Vehicle Class",
  "Fuel Type",
  "Fuel Norms",
  "Registration Date",
  "Insurance Company",
  "Insurance No",
  "Insurance Expiry",
  "Insurance Upto",
  "Fitness Upto",
  "Tax Upto",
  "PUC No",
  "PUC Upto",
  "Financier Name",
  "Registered RTO",
  "Address",
  "City Name",
  "Phone"
];

app.get("/", (req, res) => {
  res.json({
    status: "online",
    service: "Vehicle RC Intelligence Express API",
    developer: DEVELOPER_INFO,
    endpoints: {
      health: "/health",
      query: "/api/vehicle?rc=BR03H5690",
      lookup: "/lookup/BR03H5690"
    }
  });
});

app.get("/health", (req, res) => {
  res.json({
    status: "ok",
    uptime: process.uptime()
  });
});

// Normalize HTML text
function normalizeText(value) {
  return String(value || "")
    .replace(/\s+/g, " ")
    .trim();
}

// Extract fields from common label/value HTML layouts
function extractVehicleData(html) {
  const $ = cheerio.load(html);
  const data = {};

  function save(label, value) {
    const cleanLabel = normalizeText(label);
    const cleanValue = normalizeText(value);

    if (
      DESIRED_ORDER.includes(cleanLabel) &&
      cleanValue &&
      cleanValue !== cleanLabel &&
      !data[cleanLabel]
    ) {
      data[cleanLabel] = cleanValue;
    }
  }

  // Layout 1: <span>Label</span><p>Value</p>
  $("span").each((_, element) => {
    const label = normalizeText($(element).text());

    if (!DESIRED_ORDER.includes(label)) return;

    const parent = $(element).parent();
    const candidates = [
      parent.find("p").first(),
      parent.next().find("p").first(),
      $(element).next("p")
    ];

    for (const candidate of candidates) {
      if (candidate.length) {
        const value = candidate.text();
        if (normalizeText(value)) {
          save(label, value);
          break;
        }
      }
    }
  });

  // Layout 2: table rows containing label and value
  $("tr").each((_, element) => {
    const cells = $(element).find("th, td");

    if (cells.length >= 2) {
      save($(cells[0]).text(), $(cells[1]).text());
    }
  });

  // Layout 3: definition lists
  $("dt").each((_, element) => {
    save(
      $(element).text(),
      $(element).next("dd").text()
    );
  });

  // Layout 4: common label/value containers
  $("[class*='detail'], [class*='info'], [class*='field']")
    .each((_, element) => {
      const node = $(element);
      const label = normalizeText(
        node.find("span, label, strong, h3, h4").first().text()
      );

      if (!DESIRED_ORDER.includes(label)) return;

      const valueNode = node.find("p, dd").first();

      if (valueNode.length) {
        save(label, valueNode.text());
      }
    });

  const orderedData = {};

  for (const key of DESIRED_ORDER) {
    if (data[key]) orderedData[key] = data[key];
  }

  return orderedData;
}

async function vehicleLookup(req, res) {
  const rawRC =
    req.params.rc_number ||
    req.query.rc ||
    req.query.number ||
    req.query.code;

  if (!rawRC || typeof rawRC !== "string") {
    return res.status(400).json({
      status: "error",
      developer: DEVELOPER_INFO,
      message: "RC parameter is required.",
      example: "/api/vehicle?rc=BR03H5690"
    });
  }

  const rc = rawRC.replace(/[^a-zA-Z0-9]/g, "").toUpperCase();

  // Basic input validation; this is not proof that an RC exists.
  if (rc.length < 5 || rc.length > 15) {
    return res.status(400).json({
      status: "error",
      developer: DEVELOPER_INFO,
      message: "Invalid RC number format."
    });
  }

  const targetUrl =
    `https://vahanx.in/rc-search/${encodeURIComponent(rc)}`;

  try {
    const response = await axios.get(targetUrl, {
      timeout: 15000,
      maxRedirects: 5,
      responseType: "text",
      headers: {
        "User-Agent":
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) " +
          "AppleWebKit/537.36 (KHTML, like Gecko) " +
          "Chrome/131.0.0.0 Safari/537.36",
        "Accept":
          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
      }
    });

    const contentType = response.headers["content-type"] || "";

    if (
      !contentType.includes("text/html") &&
      !contentType.includes("application/xhtml+xml")
    ) {
      return res.status(502).json({
        status: "error",
        developer: DEVELOPER_INFO,
        rc,
        message:
          "The upstream server did not return an HTML page. " +
          "The source may require an API or JavaScript rendering."
      });
    }

    const data = extractVehicleData(response.data);

    if (Object.keys(data).length === 0) {
      return res.status(502).json({
        status: "error",
        developer: DEVELOPER_INFO,
        rc,
        message:
          "No vehicle details could be extracted. " +
          "The source page may have changed, blocked the request, " +
          "or requires JavaScript rendering."
      });
    }

    return res.status(200).json({
      status: "success",
      developer: DEVELOPER_INFO,
      rc,
      count: Object.keys(data).length,
      data
    });

  } catch (err) {
    const upstreamStatus = err.response?.status;

    if (upstreamStatus === 404) {
      return res.status(404).json({
        status: "error",
        developer: DEVELOPER_INFO,
        rc,
        message: "The upstream page was not found."
      });
    }

    if (err.code === "ECONNABORTED") {
      return res.status(504).json({
        status: "error",
        developer: DEVELOPER_INFO,
        rc,
        message: "The upstream request timed out. Try again later."
      });
    }

    console.error("Vehicle lookup failed:", {
      rc,
      code: err.code,
      upstreamStatus,
      message: err.message
    });

    return res.status(502).json({
      status: "error",
      developer: DEVELOPER_INFO,
      rc,
      message:
        upstreamStatus === 403
          ? "The upstream source denied access."
          : upstreamStatus
            ? `The upstream source returned HTTP ${upstreamStatus}.`
            : "Unable to connect to the upstream vehicle data source."
    });
  }
}

app.get("/api/vehicle", vehicleLookup);
app.get("/lookup/:rc_number", vehicleLookup);

app.use((req, res) => {
  res.status(404).json({
    status: "error",
    message: "Endpoint not found.",
    available: ["/", "/health", "/api/vehicle?rc=BR03H5690",
      "/lookup/BR03H5690"]
  });
});

app.listen(PORT, "0.0.0.0", () => {
  console.log(`Server listening on port ${PORT}`);
});
