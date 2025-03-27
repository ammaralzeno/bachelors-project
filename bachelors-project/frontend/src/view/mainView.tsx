import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { CloudUpload, FileText, Calculator } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { Slider } from "@/components/ui/slider"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { useMainController, Question } from "@/controller/main"

export function MainView() {
  const controller = useMainController()

  const renderQuestion = (question: Question, index: number) => {
    switch (question.Type) {
      case "inputbox":
        return (
          <div key={index} className="space-y-2">
            <Label htmlFor={`question-${index}`} className="text-indigo-900 font-medium">{question.Content}</Label>
            <Input
              id={`question-${index}`}
              value={controller.questionResponses[index]?.toString() || ""}
              onChange={(e) => controller.handleInputChange(index, e.target.value)}
              placeholder="Skriv här"
              className="border-indigo-200 focus:border-indigo-900 focus:ring-indigo-900"
              type="number"
            />
          </div>
        )
      
      case "slider": {

        const minValue = 0
        const maxValue = 64
        const currentValue = Number(controller.questionResponses[index]) || 0
        const adjustmentDescription = controller.getSliderAdjustmentDescription(currentValue)
        
        return (
          <div key={index} className="space-y-4">
            <div>
              <Label htmlFor={`question-${index}`} className="text-indigo-900 font-medium">{question.Content}</Label>
              <div className="text-sm text-indigo-700 flex justify-between">
                <span>Poäng: {currentValue}</span>
                <span>{adjustmentDescription}</span>
              </div>
            </div>
            <Slider
              id={`question-${index}`}
              defaultValue={[currentValue]}
              max={maxValue}
              min={minValue}
              step={1}
              onValueChange={(values) => controller.handleInputChange(index, values[0])}
              className="[&>span]:bg-indigo-900"
            />
            <div className="flex justify-between text-xs text-indigo-700 mt-2">
              {question.Alternatives.map((range, i) => (
                <span key={i} className="px-1">{range}</span>
              ))}
            </div>
          </div>
        )
      }
      
      case "radio": {
        const currentValue = String(controller.questionResponses[index] || question.Alternatives[0] || '')
        
        return (
          <div key={index} className="space-y-4">
            <Label className="text-indigo-900 font-medium">{question.Content}</Label>
            <RadioGroup 
              value={currentValue} 
              onValueChange={(value) => controller.handleInputChange(index, value)}
              className="flex flex-col space-y-2"
            >
              {question.Alternatives.map((option, i) => (
                <div key={i} className="flex items-center space-x-2">
                  <RadioGroupItem 
                    value={String(option)} 
                    id={`question-${index}-option-${i}`} 
                    className="border-indigo-900 text-indigo-900"
                  />
                  <Label 
                    htmlFor={`question-${index}-option-${i}`}
                    className="font-normal cursor-pointer"
                  >
                    {option}
                  </Label>
                </div>
              ))}
            </RadioGroup>
          </div>
        )
      }
      
      case "yesno": {
        const currentValue = controller.questionResponses[index]?.toString() || "Nej"
        const isYes = currentValue === "Ja"
        
        return (
          <div key={index} className="space-y-4">
            <div className="flex flex-col space-y-3">
              <Label className="text-indigo-900 font-medium">{question.Content}</Label>
              
              <div className="flex items-center space-x-6 pt-2">
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id={`question-${index}-yes`}
                    checked={isYes}
                    onCheckedChange={() => controller.handleInputChange(index, "Ja")}
                    className="border-indigo-900 data-[state=checked]:bg-indigo-900 data-[state=checked]:text-white"
                  />
                  <Label 
                    htmlFor={`question-${index}-yes`}
                    className="font-normal cursor-pointer"
                  >
                    Ja
                  </Label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <Checkbox 
                    id={`question-${index}-no`}
                    checked={!isYes}
                    onCheckedChange={() => controller.handleInputChange(index, "Nej")}
                    className="border-indigo-900 data-[state=checked]:bg-indigo-900 data-[state=checked]:text-white"
                  />
                  <Label 
                    htmlFor={`question-${index}-no`}
                    className="font-normal cursor-pointer"
                  >
                    Nej
                  </Label>
                </div>
              </div>
            </div>
          </div>
        )
      }
      
      default:
        return null
    }
  }

  const renderSummary = () => {
    return (
      <div className="mt-8 pt-6 border-t border-indigo-100">
        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <Calculator className="h-5 w-5 text-indigo-900 mr-2" />
            <h3 className="text-lg font-medium text-indigo-900">Slutresultat</h3>
          </div>
          <span className="text-xl font-bold text-indigo-900">
            {controller.formatCurrency(controller.totalSum)}
          </span>
        </div>
      </div>
    )
  }

  const renderContent = () => {
    if (controller.isEvaluating) {
      return (
        <div className="space-y-4 py-8">
          <div className="text-center mb-4">
            <FileText className="mx-auto h-12 w-12 text-indigo-900 mb-2" />
            <h3 className="text-lg font-medium text-indigo-900">Analyserar upphandlingsdokument</h3>
            <p className="text-sm text-indigo-700">Vänligen vänta medan vi analyserar ditt dokument</p>
          </div>
          <Progress value={controller.progress} className="w-full h-2 [&>div]:bg-indigo-900" />
          <p className="text-center text-sm text-indigo-700">{controller.progress}% klar</p>
        </div>
      )
    }
    
    if (controller.evaluationComplete) {
      return (
        <div className="space-y-6">
          <div className="text-center mb-4">
            <h3 className="text-lg font-medium text-indigo-900">Resultat</h3>
            <p className="text-sm text-indigo-700">Vänligen granska och fyll i följande objekt</p>
          </div>
          
          {controller.getQuestions().map((question, index) => 
            renderQuestion(question, index)
          )}
          
          {renderSummary()}
          
          <Button 
            variant="outline" 
            className="w-full border-indigo-900 text-indigo-900 hover:bg-indigo-50" 
            onClick={() => {
              // Reset states
              location.reload()
            }}
          >
            Ladda upp ett annat dokument
          </Button>
        </div>
      )
    }
    
    return (
      <>
        <div className="border-2 border-dashed border-indigo-200 rounded-md p-6 text-center hover:border-indigo-900 transition-colors">
          <CloudUpload className="mx-auto h-12 w-12 text-indigo-900 mb-2" />
          <div className="mt-2">
            <Label htmlFor="file" className="cursor-pointer text-sm font-medium text-indigo-900 hover:underline">
              {controller.fileName ? controller.fileName : "Välj en PDF-fil"}
            </Label>
            <Input
              id="file"
              type="file"
              accept=".pdf"
              className="hidden"
              onChange={controller.handleFileChange}
            />
          </div>
          <p className="text-xs text-indigo-700 mt-2">
            Stöd format: PDF
          </p>
        </div>
        
        {controller.file && !controller.uploading && (
          <Button 
            className="w-full mt-4 bg-indigo-900 hover:bg-indigo-800 text-white" 
            onClick={controller.handleEvaluate}
          >
            Analysera
          </Button>
        )}
      </>
    )
  }

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-gradient-to-b from-white to-indigo-50 p-4">
      <Card className="w-full max-w-md shadow-lg border border-indigo-100">
        <CardHeader className="border-b border-indigo-100">
          <CardTitle className="text-2xl text-center text-indigo-900">Analysera upphandlingsdokument</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          {renderContent()}
        </CardContent>
        {!controller.isEvaluating && !controller.evaluationComplete && controller.file && (
          <CardFooter>
            <Button 
              className="w-full bg-indigo-900 hover:bg-indigo-800 text-white" 
              disabled={!controller.file || controller.uploading} 
              onClick={controller.handleUpload}
            >
              {controller.uploading ? "Laddar..." : "Ladda upp PDF"}
            </Button>
          </CardFooter>
        )}
      </Card>
    </div>
  )
}
