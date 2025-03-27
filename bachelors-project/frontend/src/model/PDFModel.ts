import { Question } from "@/controller/main"
import { ApiClient, ApiQuestion, ParsedEvaluationResponse } from "@/lib/client"

export interface PDFUploadResponse {
  success: boolean
  message: string
  questions?: Question[]
}

export class PDFModel {
  private static apiClient = new ApiClient();
  private static evaluationData: ParsedEvaluationResponse | null = null;

  // mock upload
  static async uploadPDF(file: File): Promise<boolean> {
    try {
      console.log('Uploading file to backend:', file.name);
      return true;
    } catch (error) {
      console.error('Upload error:', error);
      return false;
    }
  }

  static async evaluatePDF(file: File): Promise<PDFUploadResponse> {
    try {
      // Use the API client to send the file and get evaluation components
      this.evaluationData = await this.apiClient.parseEvaluationComponents(file);
      
      return {
        success: true,
        message: "PDF evaluated successfully",
        questions: this.apiClient.convertToLocalQuestions(this.evaluationData.questions)
      };
    } catch (error) {
      console.error('Evaluation failed:', error);
      return {
        success: false,
        message: error instanceof Error ? error.message : "Unknown error occurred"
      };
    }
  }

  static getApiQuestions(): ApiQuestion[] {
    if (!this.evaluationData) {
      return [];
    }
    return this.evaluationData.questions;
  }

  static getCalculationOrder(): string[] {
    if (!this.evaluationData) {
      return [];
    }
    return this.evaluationData.calculationOrder;
  }

  // Calculate the total sum based on responses
  static calculateTotalSum(responses: Record<number, string | number>): number {
    if (!this.evaluationData) {
      // Fall back to old calculation if no API data is available
      let totalSum = 0;
      
      Object.entries(responses).forEach(([indexStr, value]) => {
        const index = parseInt(indexStr);
        
        // Handle first input (simple addition)
        if (index === 0 && typeof value === 'string') {
          const numValue = parseFloat(value) || 0;
          totalSum += numValue;
        }
        
        // Handle slider (index 1)
        if (index === 1 && typeof value === 'number') {
          totalSum += this.evaluateSliderValue(value);
        }
      });
      
      return totalSum;
    }
    
    // Convert numeric index-based responses to string id-based responses
    const apiResponses: Record<string, string | number> = {};
    
    Object.entries(responses).forEach(([indexStr, value]) => {
      const index = parseInt(indexStr);
      const question = this.evaluationData?.questions[index];
      if (question) {
        apiResponses[question.id] = value;
      }
    });
    
    // Use API client to calculate total
    return this.apiClient.calculateTotalSum(
      this.evaluationData.questions,
      apiResponses,
      this.evaluationData.calculationOrder
    );
  }

  // Get the description for a slider value adjustment (for display)
  static getSliderAdjustmentDescription(value: number): string {
    // If we have API data, use that for the description
    if (this.evaluationData) {
      // Find the slider question (assuming it's the second question with index 1)
      const sliderQuestion = this.evaluationData.questions[1];
      if (sliderQuestion) {
        return this.apiClient.getAdjustmentDescription(sliderQuestion, value);
      }
    }
    
    // Fall back to old calculation if no API data is available
    const adjustmentValue = this.evaluateSliderValue(value);
    
    if (adjustmentValue > 0) {
      return `tillägg med ${Math.abs(adjustmentValue).toLocaleString()} kr (+)`;
    } else if (adjustmentValue < 0) {
      return `avdrag med ${Math.abs(adjustmentValue).toLocaleString()} kr (-)`;
    }
    
    return "ingen justering";
  }

  // Legacy slider evaluation logic (used as fallback)
  private static evaluateSliderValue(value: number): number {
    const sliderRanges = [
      { range: "55 - 64", min: 55, max: 64, value: -600000 },
      { range: "35 - 54", min: 35, max: 54, value: -300000 },
      { range: "15 - 34", min: 15, max: 34, value: 300000 },
      { range: "0 - 14", min: 0, max: 14, value: 600000 }
    ];

    const matchingRange = sliderRanges.find(range => 
      value >= range.min && value <= range.max
    );

    return matchingRange ? matchingRange.value : 0;
  }

  // Format currency value
  static formatCurrency(value: number): string {
    return this.apiClient.formatCurrency(value);
  }
} 