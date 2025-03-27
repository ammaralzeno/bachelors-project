import { useState } from 'react'
import { Questions } from "@/lib/data"
import { PDFModel } from "@/model/PDFModel"

export type Alternative = string | number

export type Question = {
  Content: string
  Alternatives: Alternative[]
  Evaluation: unknown[]
  Type: "inputbox" | "slider" | "radio" | "yesno"
}

export interface MainController {
  file: File | null
  uploading: boolean
  fileName: string
  isEvaluating: boolean
  progress: number
  evaluationComplete: boolean
  questionResponses: Record<number, string | number>
  totalSum: number
  handleFileChange: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleUpload: () => Promise<void>
  handleEvaluate: () => void
  handleInputChange: (index: number, value: string | number) => void
  getQuestions: () => Question[]
  getSliderAdjustmentDescription: (value: number) => string
  formatCurrency: (value: number) => string
}

export function useMainController(): MainController {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [fileName, setFileName] = useState<string>("")
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [progress, setProgress] = useState(0)
  const [evaluationComplete, setEvaluationComplete] = useState(false)
  const [questionResponses, setQuestionResponses] = useState<Record<number, string | number>>({})
  const [totalSum, setTotalSum] = useState<number>(0)
  const [questions, setQuestions] = useState<Question[]>([])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      if (selectedFile.type === 'application/pdf') {
        setFile(selectedFile)
        setFileName(selectedFile.name)
        // Reset states when a new file is uploaded
        setEvaluationComplete(false)
        setIsEvaluating(false)
        setProgress(0)
        setQuestionResponses({})
        setTotalSum(0)
      } else {
        alert('Please upload a PDF file')
        e.target.value = ''
      }
    }
  }

  const handleUpload = async () => {
    if (!file) return
    
    setUploading(true)
    
    try {
      // Use the model to upload the file
      const success = await PDFModel.uploadPDF(file)
      if (!success) {
        throw new Error("Upload failed")
      }
    } catch (error) {
      console.error('Upload failed:', error)
    } finally {
      setUploading(false)
    }
  }

  const handleEvaluate = () => {
    if (!file) return
    
    setIsEvaluating(true)
    setProgress(0)
    
    // Progress simulation for better UX
    const progressInterval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + 10
        if (newProgress >= 90) {
          clearInterval(progressInterval)
        }
        return newProgress
      })
    }, 300)
    
    PDFModel.evaluatePDF(file)
      .then(response => {

        clearInterval(progressInterval)
        // Set progress to 100% when evaluation is complete
        setProgress(100)
        
        if (response.success && response.questions) {
          setTimeout(() => {
            setIsEvaluating(false)
            setEvaluationComplete(true)
            
            // Store the questions
            setQuestions(response.questions || [])
            
            // Set default values for questions
            const initialResponses: Record<number, string | number> = {}
            const questionList = response.questions || [];
            questionList.forEach((q, index) => {
              if (q.Type === "inputbox") {
                initialResponses[index] = ""
              } else if (q.Type === "slider") {
                initialResponses[index] = 0
              } else if (q.Type === "radio" && q.Alternatives.length > 0) {
                initialResponses[index] = q.Alternatives[0]
              } else if (q.Type === "yesno") {
                initialResponses[index] = "Nej" // Default to "No"
              }
            })
            setQuestionResponses(initialResponses)
            
            // Calculate initial total sum
            setTotalSum(PDFModel.calculateTotalSum(initialResponses))
          }, 500)
        } else {
          console.error('Evaluation failed:', response.message)
          setIsEvaluating(false)
          alert(`Evaluation failed: ${response.message}`)
        }
      })
      .catch(error => {
        console.error('Evaluation failed:', error)
        setIsEvaluating(false)
        clearInterval(progressInterval)
        alert('Failed to evaluate PDF. Please try again.')
      })
  }

  const handleInputChange = (index: number, value: string | number) => {
    const updatedResponses = {
      ...questionResponses,
      [index]: value
    };
    
    setQuestionResponses(updatedResponses);
    
    // Recalculate the total sum whenever inputs change
    const newTotalSum = PDFModel.calculateTotalSum(updatedResponses);
    setTotalSum(newTotalSum);
  }
  
  const getQuestions = (): Question[] => {
    // Use the stored questions if we have them, otherwise fall back to static data
    return questions.length > 0 ? questions : (Questions as unknown as Question[])
  }
  
  const getSliderAdjustmentDescription = (value: number): string => {
    return PDFModel.getSliderAdjustmentDescription(value);
  }
  
  const formatCurrency = (value: number): string => {
    return PDFModel.formatCurrency(value);
  }

  return {
    file,
    uploading,
    fileName,
    isEvaluating,
    progress,
    evaluationComplete,
    questionResponses,
    totalSum,
    handleFileChange,
    handleUpload,
    handleEvaluate,
    handleInputChange,
    getQuestions,
    getSliderAdjustmentDescription,
    formatCurrency
  }
}
