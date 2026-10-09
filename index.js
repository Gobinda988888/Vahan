const express = require("express");
const axios = require("axios");
const cheerio = require("cheerio");

const app = express();
const PORT = process.env.PORT || 10000;

const DEVELOPER_INFO = {
  name: "Sudhirxd",
  github: "https://github.com/Sudhirxd",
  instagram: "https://www.instagram.com/sudhirxd.in",
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

// Health check
app.get("/", (req, res) => {
  res.json({
    status: "online",
    service: "Vehicle RC Intelligence API",
    version: "2.0",
    endpoints: {
      query: "/api/vehicle?rc=BR03H5690",
      lookup: "/lookup/BR03H5690"
    }
  });
});

// Shared vehicle lookup handler
async function handleVehicleLookup(req, res) {
  const rcNumber =
    req.params.rc_number ||
    req.query.rc ||
    req.query.number ||
    req.query.code;

  if (!rcNumber) {
    return res.status(400).json({
      status: "error",
      message: "RC parameter is required",
      example: "/api/vehicle?rc=BR03H5690"
    });
  }

  const rcClean = String(rcNumber)
    .replace(/[^a-zA-Z0-9]/g, "")
    .toUpperCase();

  if (rcClean.length < 4 || rcClean.length > 15) {
    return res.status(400).json({
      status: "error",
      message: "Invalid registration number format"
    });
  }

  const targetUrl =
    `https://vahanx.in/rc-search/${encodeURIComponent(rcClean)}`;

  try {
    const response = await axios.get(targetUrl, {
      timeout: 15000,
      headers: {
        "User-Agent": "Mozilla/5.0 (compatible; VehicleInfoAPI/2.0)",
        "Accept": "text/html,application/xhtml+xml"
      },
      maxRedirects: 5
    });

    const $ = cheerio.load(response.data);
    const data = {};

    // Extract fields from the page.
    for (const key of DESIRED_ORDER) {
      $("span").each((_, el) => {
        if ($(el).text().trim() !== key) return;

        const parent = $(el).parent();
        const value =
          parent.find("p").first().text().trim() ||
          $(el).closest("div").find("p").first().text().trim();

        if (value) {
          data[key] = value;
        }
      });
    }

    if (Object.keys(data).length === 0) {
      return res.status(404).json({
        status: "error",
        rc: rcClean,
        message:
          "No details extracted. The record may be unavailable or the upstream page structure may have changed."
      });
    }

    return res.json({
      status: "success",
      rc: rcClean,
      data
    });
  } catch (err) {
    const upstreamStatus = err.response?.status;

    console.error("Vehicle lookup failed:", {
      status: upstreamStatus || null,
      message: err.message
    });

    if (upstreamStatus === 404) {
      return res.status(404).json({
        status: "error",
        rc: rcClean,
        message: "No record found by the upstream website"
      });
    }

    if (upstreamStatus === 403 || upstreamStatus === 429) {
      return res.status(502).json({
        status: "error",
        message: "Upstream website denied or rate-limited the request"
      });
    }

    return res.status(502).json({
      status: "error",
      message: "Unable to fetch data from the upstream website"
    });
  }
}

// API routes
app.get("/api/vehicle", handleVehicleLookup);
app.get("/lookup/:rc_number", handleVehicleLookup);

// Unknown routes
app.use((req, res) => {
  res.status(404).json({
    status: "error",
    message: "Route not found",
    path: req.path,
    availableEndpoints: [
      "/",
      "/api/vehicle?rc=BR03H5690",
      "/lookup/BR03H5690"
    ]
  });
});

// Start server
app.listen(PORT, "0.0.0.0", () => {
  console.log(`Vehicle RC API running on port ${PORT}`);
});
