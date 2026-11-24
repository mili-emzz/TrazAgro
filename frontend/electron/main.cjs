const { app, BrowserWindow, Menu, shell } = require('electron');
const path = require('path');

const isProd = process.argv.includes('--prod') || app.isPackaged;
const DEV_URL = process.env.TRAZAAGRO_DEV_URL || 'http://127.0.0.1:5173';

function createMainWindow() {
  const win = new BrowserWindow({
    width: 1340,
    height: 860,
    minWidth: 1024,
    minHeight: 680,
    title: 'TrazaAgro · Trazabilidad Políglota',
    backgroundColor: '#F1FAEE',
    autoHideMenuBar: true,
    webPreferences: {
      preload: path.join(__dirname, 'preload.cjs'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  // Abrir enlaces externos en el navegador del sistema
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (url.startsWith('http://') || url.startsWith('https://')) {
      shell.openExternal(url);
      return { action: 'deny' };
    }
    return { action: 'allow' };
  });

  if (isProd) {
    win.loadFile(path.join(__dirname, '..', 'dist', 'index.html'));
  } else {
    win.loadURL(DEV_URL);
  }
}

app.whenReady().then(() => {
  // Menú minimalista nativo para escritorio
  const menuTemplate = [
    {
      label: 'TrazaAgro',
      submenu: [
        { role: 'reload', label: 'Recargar vista' },
        { role: 'toggleDevTools', label: 'Herramientas de desarrollo' },
        { type: 'separator' },
        { role: 'quit', label: 'Salir de TrazaAgro' },
      ],
    },
    {
      label: 'Ver',
      submenu: [
        { role: 'resetZoom', label: 'Zoom 100%' },
        { role: 'zoomIn', label: 'Acercar' },
        { role: 'zoomOut', label: 'Alejar' },
        { type: 'separator' },
        { role: 'togglefullscreen', label: 'Pantalla completa' },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(menuTemplate));

  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
