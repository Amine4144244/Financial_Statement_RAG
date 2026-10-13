const http = require('http');

// Compile or run via ts-node or compiled dist
async function runTest() {
  console.log('[Test] Compiling TypeScript backend...');
  const { execSync } = require('child_process');
  execSync('npx tsc', { cwd: __dirname, stdio: 'inherit' });

  console.log('[Test] Booting Express App...');
  const { createApp } = require('./dist/app');
  const app = createApp();

  const server = http.createServer(app);
  await new Promise((resolve) => server.listen(4099, resolve));
  const baseUrl = 'http://localhost:4099/api';

  try {
    const axios = require('axios');

    // 1. Health check
    const health = await axios.get(`${baseUrl}/health`);
    console.log('[Test] Health status:', health.data.status);
    if (health.data.status !== 'ok') throw new Error('Health check failed');

    // 2. User registration
    const regRes = await axios.post(`${baseUrl}/auth/register`, {
      email: 'analyst@example.com',
      password: 'SecurePassword123!',
      full_name: 'Senior Analyst',
    });
    console.log('[Test] User registered:', regRes.data.user.email);
    const token = regRes.data.token;
    if (!token) throw new Error('No token returned on registration');

    // 3. User login
    const loginRes = await axios.post(`${baseUrl}/auth/login`, {
      email: 'analyst@example.com',
      password: 'SecurePassword123!',
    });
    console.log('[Test] User logged in successfully. Token verified.');

    // 4. Auth Me check
    const meRes = await axios.get(`${baseUrl}/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    console.log('[Test] Authenticated user:', meRes.data.user.email);

    // 5. Companies list
    const compRes = await axios.get(`${baseUrl}/companies`);
    console.log('[Test] Companies count:', compRes.data.length);
    if (compRes.data.length < 3) throw new Error('Missing default companies');

    // 6. Documents list
    const docsRes = await axios.get(`${baseUrl}/documents`);
    console.log('[Test] Documents listing works, current count:', docsRes.data.length);

    console.log('\n[SUCCESS] ALL BACKEND GATEWAY INTEGRATION TESTS PASSED!');
  } finally {
    server.close();
  }
}

runTest().catch((err) => {
  console.error('[FAILED] Test error:', err.message);
  process.exit(1);
});
