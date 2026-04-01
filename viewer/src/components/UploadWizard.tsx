import { useState } from 'react'
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, ArrowRight, ArrowLeft } from 'lucide-react'

interface UploadWizardProps {
  onSidecarGenerated: (sidecar: any) => void
  onClose?: () => void
}

type Step = 1 | 2 | 3

interface IFCData {
  project_name: string
  building_name: string | null
  walls: number
  roofs: number
  slabs: number
  windows: number
  doors: number
  total_elements: number
}

interface EVEBIData {
  project_name: string
  materials: number
  constructions: number
  elements: number
  zones: number
}

interface MappingPreview {
  total_ifc: number
  total_evebi: number
  potential_matches: number
  match_rate: number
}

export function UploadWizard({ onSidecarGenerated, onClose }: UploadWizardProps) {
  const [currentStep, setCurrentStep] = useState<Step>(1)
  
  // Step 1: IFC
  const [ifcFile, setIfcFile] = useState<File | null>(null)
  const [ifcData, setIfcData] = useState<IFCData | null>(null)
  const [ifcLoading, setIfcLoading] = useState(false)
  const [ifcError, setIfcError] = useState<string | null>(null)
  
  // Step 2: EVEBI
  const [evebiFile, setEvebiFile] = useState<File | null>(null)
  const [evebiData, setEvebiData] = useState<EVEBIData | null>(null)
  const [mappingPreview, setMappingPreview] = useState<MappingPreview | null>(null)
  const [evebiLoading, setEvebiLoading] = useState(false)
  const [evebiError, setEvebiError] = useState<string | null>(null)
  
  // Step 3: Final
  const [finalLoading, setFinalLoading] = useState(false)
  const [finalError, setFinalError] = useState<string | null>(null)

  // Step 1: IFC Upload
  const handleIfcUpload = async (file: File) => {
    if (!file.name.endsWith('.ifc')) {
      setIfcError('Datei muss .ifc Extension haben')
      return
    }

    setIfcFile(file)
    setIfcLoading(true)
    setIfcError(null)

    try {
      const formData = new FormData()
      formData.append('ifc_file', file)

      const response = await fetch('http://localhost:8000/parse-ifc', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Fehler beim Parsen')
      }

      const data = await response.json()
      setIfcData(data)
    } catch (err) {
      setIfcError(err instanceof Error ? err.message : 'Unbekannter Fehler')
      setIfcFile(null)
    } finally {
      setIfcLoading(false)
    }
  }

  // Step 2: EVEBI Upload
  const handleEvebiUpload = async (file: File) => {
    if (!file.name.endsWith('.evea') && !file.name.endsWith('.evex')) {
      setEvebiError('Datei muss .evea oder .evex Extension haben')
      return
    }

    setEvebiFile(file)
    setEvebiLoading(true)
    setEvebiError(null)

    try {
      const formData = new FormData()
      formData.append('evebi_file', file)
      if (ifcFile) {
        formData.append('ifc_file', ifcFile)
      }

      const response = await fetch('http://localhost:8000/parse-evebi', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Fehler beim Parsen')
      }

      const data = await response.json()
      setEvebiData(data.evebi_data)
      setMappingPreview(data.mapping_preview)
    } catch (err) {
      setEvebiError(err instanceof Error ? err.message : 'Unbekannter Fehler')
      setEvebiFile(null)
    } finally {
      setEvebiLoading(false)
    }
  }

  // Step 3: Generate Sidecar
  const handleGenerateSidecar = async () => {
    if (!ifcFile || !evebiFile) return

    setFinalLoading(true)
    setFinalError(null)

    try {
      const formData = new FormData()
      formData.append('ifc_file', ifcFile)
      formData.append('evebi_file', evebiFile)

      const response = await fetch('http://localhost:8000/generate-sidecar', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Fehler beim Verarbeiten')
      }

      const result = await response.json()
      
      console.log('✅ Sidecar generiert:', result)
      console.log('📊 Stats:', result.stats)
      
      if (result.success) {
        onSidecarGenerated(result.sidecar)
      } else {
        throw new Error('Verarbeitung fehlgeschlagen')
      }
    } catch (err) {
      setFinalError(err instanceof Error ? err.message : 'Unbekannter Fehler')
    } finally {
      setFinalLoading(false)
    }
  }

  const canProceedToStep2 = ifcFile && ifcData && !ifcError
  const canProceedToStep3 = canProceedToStep2 && evebiFile && evebiData && !evebiError

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {/* Step 1 */}
          <div className="flex items-center flex-1">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
              currentStep >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              {currentStep > 1 ? <CheckCircle2 size={20} /> : '1'}
            </div>
            <div className="ml-3">
              <div className="text-sm font-medium">IFC-Datei</div>
              <div className="text-xs text-gray-500">Geometrie hochladen</div>
            </div>
          </div>

          <div className={`flex-1 h-1 mx-4 ${currentStep >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />

          {/* Step 2 */}
          <div className="flex items-center flex-1">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
              currentStep >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              {currentStep > 2 ? <CheckCircle2 size={20} /> : '2'}
            </div>
            <div className="ml-3">
              <div className="text-sm font-medium">EVEBI-Datei</div>
              <div className="text-xs text-gray-500">Energiedaten hochladen</div>
            </div>
          </div>

          <div className={`flex-1 h-1 mx-4 ${currentStep >= 3 ? 'bg-blue-600' : 'bg-gray-200'}`} />

          {/* Step 3 */}
          <div className="flex items-center flex-1">
            <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${
              currentStep >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'
            }`}>
              3
            </div>
            <div className="ml-3">
              <div className="text-sm font-medium">Bestätigen</div>
              <div className="text-xs text-gray-500">Sidecar erstellen</div>
            </div>
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow-lg p-6 min-h-[400px]">
        {/* Step 1: IFC Upload */}
        {currentStep === 1 && (
          <div>
            <h2 className="text-xl font-bold mb-4">Schritt 1: IFC-Datei hochladen</h2>
            <p className="text-gray-600 mb-6">
              Laden Sie Ihre IFC-Datei hoch. Wir extrahieren die Geometrie-Daten (Wände, Dächer, Fenster, etc.).
            </p>

            {/* Upload Area */}
            {!ifcFile && (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  accept=".ifc"
                  onChange={(e) => e.target.files?.[0] && handleIfcUpload(e.target.files[0])}
                  className="hidden"
                  id="ifc-upload"
                  disabled={ifcLoading}
                />
                <label htmlFor="ifc-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <div className="text-lg font-medium mb-2">IFC-Datei auswählen</div>
                  <div className="text-sm text-gray-500">oder Datei hierher ziehen</div>
                </label>
              </div>
            )}

            {/* Loading */}
            {ifcLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mr-3" />
                <span className="text-lg">IFC-Datei wird analysiert...</span>
              </div>
            )}

            {/* Error */}
            {ifcError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-red-700">{ifcError}</div>
              </div>
            )}

            {/* Success - Show Data */}
            {ifcData && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-medium text-green-700">IFC-Datei erfolgreich geladen</div>
                    <div className="text-sm text-green-600 mt-1">{ifcFile?.name}</div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="font-semibold mb-4">Extrahierte Daten:</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-gray-500">Projekt</div>
                      <div className="font-medium">{ifcData.project_name}</div>
                    </div>
                    {ifcData.building_name && (
                      <div>
                        <div className="text-sm text-gray-500">Gebäude</div>
                        <div className="font-medium">{ifcData.building_name}</div>
                      </div>
                    )}
                    <div>
                      <div className="text-sm text-gray-500">Wände</div>
                      <div className="font-medium">{ifcData.walls}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Dächer</div>
                      <div className="font-medium">{ifcData.roofs}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Böden</div>
                      <div className="font-medium">{ifcData.slabs}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Fenster</div>
                      <div className="font-medium">{ifcData.windows}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Türen</div>
                      <div className="font-medium">{ifcData.doors}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Gesamt</div>
                      <div className="font-medium text-blue-600">{ifcData.total_elements} Elemente</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 2: EVEBI Upload */}
        {currentStep === 2 && (
          <div>
            <h2 className="text-xl font-bold mb-4">Schritt 2: EVEBI-Datei hochladen</h2>
            <p className="text-gray-600 mb-6">
              Laden Sie Ihre EVEBI .evea Datei hoch. Wir verknüpfen die Energiedaten mit der IFC-Geometrie.
            </p>

            {/* Upload Area */}
            {!evebiFile && (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  accept=".evea"
                  onChange={(e) => e.target.files?.[0] && handleEvebiUpload(e.target.files[0])}
                  className="hidden"
                  id="evebi-upload"
                  disabled={evebiLoading}
                />
                <label htmlFor="evebi-upload" className="cursor-pointer">
                  <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                  <div className="text-lg font-medium mb-2">EVEBI .evea Datei auswählen</div>
                  <div className="text-sm text-gray-500">oder Datei hierher ziehen</div>
                </label>
              </div>
            )}

            {/* Loading */}
            {evebiLoading && (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600 mr-3" />
                <span className="text-lg">EVEBI-Datei wird analysiert...</span>
              </div>
            )}

            {/* Error */}
            {evebiError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-red-700">{evebiError}</div>
              </div>
            )}

            {/* Success - Show Data */}
            {evebiData && mappingPreview && (
              <div className="space-y-4">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start">
                  <CheckCircle2 className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                  <div>
                    <div className="text-sm font-medium text-green-700">EVEBI-Datei erfolgreich geladen</div>
                    <div className="text-sm text-green-600 mt-1">{evebiFile?.name}</div>
                  </div>
                </div>

                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="font-semibold mb-4">Extrahierte Daten:</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-gray-500">Projekt</div>
                      <div className="font-medium">{evebiData.project_name}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Materialien</div>
                      <div className="font-medium">{evebiData.materials}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Konstruktionen</div>
                      <div className="font-medium">{evebiData.constructions}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Bauteile</div>
                      <div className="font-medium">{evebiData.elements}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Zonen</div>
                      <div className="font-medium">{evebiData.zones}</div>
                    </div>
                  </div>
                </div>

                <div className="bg-blue-50 rounded-lg p-6">
                  <h3 className="font-semibold mb-4">Mapping-Vorschau:</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">IFC-Elemente:</span>
                      <span className="font-medium">{mappingPreview.total_ifc}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">EVEBI-Elemente:</span>
                      <span className="font-medium">{mappingPreview.total_evebi}</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Mögliche Matches:</span>
                      <span className="font-medium">{mappingPreview.potential_matches}</span>
                    </div>
                    <div className="flex justify-between items-center pt-3 border-t border-blue-200">
                      <span className="text-sm font-medium">Erwartete Match-Rate:</span>
                      <span className={`font-bold text-lg ${
                        mappingPreview.match_rate >= 0.8 ? 'text-green-600' :
                        mappingPreview.match_rate >= 0.5 ? 'text-yellow-600' :
                        'text-red-600'
                      }`}>
                        {Math.round(mappingPreview.match_rate * 100)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Confirm & Generate */}
        {currentStep === 3 && (
          <div>
            <h2 className="text-xl font-bold mb-4">Schritt 3: Sidecar erstellen</h2>
            <p className="text-gray-600 mb-6">
              Prüfen Sie die Daten und erstellen Sie das DIN18599 Sidecar JSON.
            </p>

            <div className="space-y-4">
              {/* IFC Summary */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileText className="w-5 h-5 text-blue-600 mr-3" />
                    <div>
                      <div className="font-medium">IFC-Datei</div>
                      <div className="text-sm text-gray-500">{ifcFile?.name}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-500">Elemente</div>
                    <div className="font-medium">{ifcData?.total_elements}</div>
                  </div>
                </div>
              </div>

              {/* EVEBI Summary */}
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <FileText className="w-5 h-5 text-green-600 mr-3" />
                    <div>
                      <div className="font-medium">EVEBI-Datei</div>
                      <div className="text-sm text-gray-500">{evebiFile?.name}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-sm text-gray-500">Bauteile</div>
                    <div className="font-medium">{evebiData?.elements}</div>
                  </div>
                </div>
              </div>

              {/* Mapping Preview */}
              {mappingPreview && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">Erwartete Match-Rate</div>
                      <div className="text-sm text-gray-600">Automatisches Mapping via PosNo/Name/Geometrie</div>
                    </div>
                    <div className={`text-2xl font-bold ${
                      mappingPreview.match_rate >= 0.8 ? 'text-green-600' :
                      mappingPreview.match_rate >= 0.5 ? 'text-yellow-600' :
                      'text-red-600'
                    }`}>
                      {Math.round(mappingPreview.match_rate * 100)}%
                    </div>
                  </div>
                </div>
              )}

              {/* Error */}
              {finalError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start">
                  <AlertCircle className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-red-700">{finalError}</div>
                </div>
              )}

              {/* Generate Button */}
              <button
                onClick={handleGenerateSidecar}
                disabled={finalLoading}
                className={`w-full py-4 rounded-lg font-medium text-white transition-colors flex items-center justify-center ${
                  finalLoading
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-green-600 hover:bg-green-700'
                }`}
              >
                {finalLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Sidecar wird erstellt...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-5 h-5 mr-2" />
                    Sidecar jetzt erstellen
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Buttons */}
      <div className="mt-6 flex justify-between">
        <button
          onClick={() => {
            if (currentStep > 1) setCurrentStep((currentStep - 1) as Step)
            else if (onClose) onClose()
          }}
          className="px-6 py-2 rounded-lg border border-gray-300 hover:bg-gray-50 transition-colors flex items-center"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          {currentStep === 1 ? 'Abbrechen' : 'Zurück'}
        </button>

        {currentStep < 3 && (
          <button
            onClick={() => setCurrentStep((currentStep + 1) as Step)}
            disabled={
              (currentStep === 1 && !canProceedToStep2) ||
              (currentStep === 2 && !canProceedToStep3)
            }
            className={`px-6 py-2 rounded-lg font-medium transition-colors flex items-center ${
              ((currentStep === 1 && !canProceedToStep2) || (currentStep === 2 && !canProceedToStep3))
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            Weiter
            <ArrowRight className="w-4 h-4 ml-2" />
          </button>
        )}
      </div>
    </div>
  )
}
