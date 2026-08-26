import re

with open("client/src/main.tsx", "r", encoding="utf-8") as f:
    content = f.read()

imports = """import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import './index.css'
import App from './App.tsx'

const theme = createTheme({
  palette: {
    primary: {
      main: '#40AA40',
    },
  },
})
"""

render = """createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <App />
    </ThemeProvider>
  </StrictMode>,
)
"""

content = re.sub(r"import \{ StrictMode \}.*?import App from '\./App\.tsx'", imports, content, flags=re.DOTALL)
content = re.sub(r"createRoot\(document\.getElementById\('root'\)!\)\.render\(.*?\)", render, content, flags=re.DOTALL)

with open("client/src/main.tsx", "w", encoding="utf-8") as f:
    f.write(content)
