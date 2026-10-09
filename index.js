const express = require('express');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.get('/', (req, res) => {
  res.send('VehicleInfo API proxy is running on Render.');
});

// Endpoint: /rc?num=JH05DE7988
app.get('/rc', async (req, res) => {
  const rcNumber = (req.query.num || 'JH05DE7988').trim().toUpperCase().replace(/[^A-Z0-9]/g, '');

  if (!rcNumber) {
    return res.status(400).json({ error: 'registration_number is required' });
  }

  const url = 'https://api-ct.vehicleinfo.app/gw/plt/bffctsvc/api/v1/garage/rc-search';

  const params = {
    registration_number: rcNumber
  };

  const headers = {
    'User-Agent': 'okhttp/4.12.0',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Encoding': 'gzip',
    'authorization': 'Bearer eyJhbGciOiJFUzI1NiIsImtpZCI6IjI2YjM0NDgwLWQ5ZDEtNDQ4NS1iYzczLTRiN2IxOGJiOWUyNCIsInR5cCI6IkpXVCJ9.eyJhdWQiOltdLCJjbGllbnRfaWQiOiJjbGllbnRfWXVGVmVodWdxV2tOTkJLOTNIZ1Q0dyIsImV4cCI6MTc4OTkyMTIxNiwiZXh0Ijp7Imdyb3VwX2lkIjoiNThhNGQ5MzEtMTZhZi00MGY5LWI0ZmYtOGExNDU4YzA2ZjNkIiwic2Vzc2lvbl9pZCI6ImEyNWVhMWMxLTBiZTMtNDY2NS05MjIyLWMyOWNlZjM5M2Y5NiIsInVzZXJfdHlwZSI6IkVYVEVSTkFMIn0sImlhdCI6MTc4ODcxMTYxNSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmNhcnMyNC5jb20vIiwianRpIjoiMDNlNDNhMzItOGU3Yy00ODRhLTlmYzktYTc1MjBlNmM1YjIyIiwibmJmIjoxNzg4NzExNjE1LCJzY3AiOlsib2ZmbGluZV9hY2Nlc3MiXSwic3ViIjoiNmY0YWQ5ZjktOGRiMy00NGVlLWFhNDUtZjJlM2Q1YTYxNmQxIn0.p96b8srL3ybB0lMC-B9HN-0lpsFr4q5kGgOTLbXpoK26wDwbOp4EY-b0SpcZdyJn8ysIqb5CbTzFQEY2Z4fE5g',
    'x-user-city-id': '777',
    'super_app_source': 'vehicleinfo_consumerapp',
    'x-api-key': 'c91f6a2e4b78d0c5a31b2f8d7e09c3fa',
    'x_app_instance_id': '547247478ea8e416185d98fbeb629954',
    'x-device-id': '547247478ea8e416185d98fbeb629954',
    'x-tenant-id': 'VI_INDIA',
    'userid': '6f4ad9f9-8db3-44ee-aa45-f2e3d5a616d1',
    'x_experiment_id': '252935e1-2b91-4b74-9734-9a40037cd09f',
    'clientid': 'vehicleinfo_consumerapp',
    'appversion': '323',
    'osname': 'android',
    'useragent': 'vehicleinfo_consumerapp/323',
    'source': 'MobileApp',
    'x_country': 'IN',
    'x-tenant-slug': 'vehicleinfo'
  };

  try {
    const response = await axios.get(url, {
      params,
      headers,
      timeout: 15000
    });
    res.json(response.data);
  } catch (error) {
    res.status(error.response ? error.response.status : 500).json({
      error: error.message,
      data: error.response ? error.response.data : null
    });
  }
});

app.listen(PORT, () => {
  console.log(`Server listening on port ${PORT}`);
});
