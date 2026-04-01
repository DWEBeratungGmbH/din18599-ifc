import { useState } from 'react'
import { Upload, FileText, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'

interface FileUploadProps {
  onSidecarGenerated: (sidecar: any) => void
}

export function FileUpload({ onSidecarGenerated }: FileUploadProps) {
  const [ifcFile, setIfcFile] = useState<File | null>(null)
  const [evebiFile, setEvebiFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [stats, setStats] = useState<any>(null)

  const handleIfcChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (!file.name.endsWith('.ifc')) {
        setError('IFC-Datei muss .ifc Extension haben')
        return
      }
      setIfcFile(file)
      setError(null)
    }
  }

  const handleEvebiChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      if (!file.name.endsWith('.evea')) {
        setError('EVEBI-Datei muss .evea Extension haben')
        return
      }
      setEvebiFile(file)
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!ifcFile || !evebiFile) {
      setError('Bitte beide Dateien auswählen')
      return
    }

    setIsProcessing(true)
    setError(null)
    setSuccess(false)

    try {
      const formData = new FormData()
      formData.append('ifc_file', ifcFile)
      formData.append('evebi_file', evebiFile)

      const response = await fetch('http://localhost:8000/process', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Fehler beim Verarbeiten')
      }

      const result = await response.json()
      
      if (result.success) {
        setSuccess(true)
        setStats(result.stats)
        onSidecarGenerated(result.sidecar)
      } else {
        throw new Error('Verarbeitung fehlgeschlagen')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler')
    } finally {
      setIsProcessing(false)
    }
  }

  const handleReset = () => {
    setIfcFile(null)
    setEvebiFile(null)
    setError(null)
    setSuccess(false)
    setStats(null)
  }

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          IFC + EVEBI Upload
        </h2>
        <p className="text-gray-600">
          Laden Sie Ihre IFC-Datei und EVEBI-Archiv hoch, um ein DIN18599 Sidecar JSON zu generieren.
        </p>
      </div>

      {/* IFC Upload */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          IFC-Datei (Geometrie)
        </label>
        <div className="relative">
          <input
            type="file"
            accept=".ifc"
            onChange={handleIfcChange}
            className="hidden"
            id="ifc-upload"
            disabled={isProcessing}
          />
          <label
            htmlFor="ifc-upload"
            className={`flex items-center justify-center w-full px-4 py-3 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
              ifcFile
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-gray-400 bg-gray-50'
            } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <FileText className="w-5 h-5 mr-2 text-gray-500" />
            <span className="text-sm text-gray-700">
              {ifcFile ? ifcFile.name : 'IFC-Datei auswählen'}
            </span>
          </label>
        </div>
      </div>

      {/* EVEBI Upload */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          EVEBI-Archiv (.evea)
        </label>
        <div className="relative">
          <input
            type="file"
            accept=".evea"
            onChange={handleEvebiChange}
            className="hidden"
            id="evebi-upload"
            disabled={isProcessing}
          />
          <label
            htmlFor="evebi-upload"
            className={`flex items-center justify-center w-full px-4 py-3 border-2 border-dashed rounded-lg cursor-pointer transition-colors ${
              evebiFile
                ? 'border-green-500 bg-green-50'
                : 'border-gray-300 hover:border-gray-400 bg-gray-50'
            } ${isProcessing ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            <FileText className="w-5 h-5 mr-2 text-gray-500" />
            <span className="text-sm text-gray-700">
              {evebiFile ? evebiFile.name : 'EVEBI-Archiv auswählen'}
            </span>
          </label>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start">
          <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
          <div className="text-sm text-red-700">{error}</div>
        </div>
      )}

      {/* Success Message */}
      {success && stats && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-start mb-2">
            <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
            <div className="text-sm text-green-700 font-medium">
              Sidecar erfolgreich generiert!
            </div>
          </div>
          <div className="ml-7 text-sm text-green-600 space-y-1">
            <div>✓ {stats.matched} Elemente gemappt ({Math.round(stats.match_rate * 100)}%)</div>
            <div>✓ {stats.total_ifc} IFC-Elemente verarbeitet</div>
            <div>✓ {stats.total_evebi} EVEBI-Elemente verarbeitet</div>
            {stats.unmatched_ifc > 0 && (
              <div className="text-yellow-600">⚠ {stats.unmatched_ifc} IFC-Elemente nicht gemappt</div>
            )}
            {stats.unmatched_evebi > 0 && (
              <div className="text-yellow-600">⚠ {stats.unmatched_evebi} EVEBI-Elemente nicht gemappt</div>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex gap-3">
        <button
          onClick={handleUpload}
          disabled={!ifcFile || !evebiFile || isProcessing}
          className={`flex-1 flex items-center justify-center px-4 py-3 rounded-lg font-medium transition-colors ${
            !ifcFile || !evebiFile || isProcessing
              ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 mr-2 animate-spin" />
              Verarbeite...
            </>
          ) : (
            <>
              <Upload className="w-5 h-5 mr-2" />
              Sidecar generieren
            </>
          )}
        </button>

        {(ifcFile || evebiFile || success) && (
          <button
            onClick={handleReset}
            disabled={isProcessing}
            className="px-4 py-3 rounded-lg font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 transition-colors disabled:opacity-50"
          >
            Zurücksetzen
          </button>
        )}
      </div>

      {/* Info */}
      <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <div className="text-sm text-blue-800">
          <strong>Hinweis:</strong> Die Dateien werden lokal verarbeitet und nicht gespeichert.
          Der generierte Sidecar kann anschließend heruntergeladen werden.
        </div>
      </div>
    </div>
  )
}
