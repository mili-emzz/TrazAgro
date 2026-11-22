const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('trazaDesktop', {
  isDesktop: true,
  platform: process.platform,
});
