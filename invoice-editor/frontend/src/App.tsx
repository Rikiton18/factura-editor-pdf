import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { UploadPage } from './pages/UploadPage'
import { EditorPage } from './pages/EditorPage'
import { DemoPage } from './pages/DemoPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/editor/:sessionId" element={<EditorPage />} />
        <Route path="/demo/:sessionId" element={<DemoPage />} />
      </Routes>
    </BrowserRouter>
  )
}
