import { createApp } from './app';
import { config } from './config';

const app = createApp();

app.listen(config.port, () => {
  console.log(`[Backend Gateway] Running at http://localhost:${config.port}`);
  console.log(`[Backend Gateway] Connected to AI Service at ${config.aiServiceUrl}`);
});
