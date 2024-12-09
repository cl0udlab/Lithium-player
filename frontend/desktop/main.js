import { app, BrowserWindow } from 'electron'
import path from 'path'
import { fileURLToPath } from 'url'
import serve from 'electron-serve'

const loadURL = serve({ directory: '.' })

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

let mainWindow

const isdev = !app.isPackaged

function createWindow() {
	mainWindow = new BrowserWindow({
		width: 800,
		height: 600,
		webPreferences: {
			nodeIntegration: true,
			webSecurity: false
		},
		icon: path.join(__dirname, 'static/favicon.png'),
		show: false
	})

	if (isdev) {
		mainWindow.loadURL('http://localhost:5173/')
	} else {
		loadURL(mainWindow)
	}
	// if(!isdev) mainWindow.removeMenu()

	mainWindow.on('closed', function () {
		mainWindow = null
	})

	mainWindow.once('ready-to-show', () => {
		mainWindow.show()
	})
}

app.on('ready', createWindow)
app.on('window-all-closed', function () {
	if (process.platform !== 'darwin') app.quit()
})
app.on('activate', function () {
	if (mainWindow === null) createWindow()
})
