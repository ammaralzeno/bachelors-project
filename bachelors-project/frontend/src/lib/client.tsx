import { Question as LocalQuestion } from "@/controller/main";

export interface ApiQuestion {
  id: string;
  content: string;
  type: string;
  alternatives: string[];
  evaluation: {
    operation: "base" | "adjust" | "percent";
    valueType: "direct" | "range" | "map";
    ranges?: Array<{
      min: number;
      max: number;
      value: number;
    }>;
    mapping?: Record<string, number>;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  message?: string;
  data?: T;
  error?: string;
}

export interface ParsedEvaluationResponse {
  success: boolean;
  questions: ApiQuestion[];
  calculationOrder: string[];
}

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = 'http://127.0.0.1:8000') {
    this.baseUrl = baseUrl;
  }

  /**
   * Uploads a PDF file and gets the parsed evaluation components
   */
  async parseEvaluationComponents(file: File): Promise<ParsedEvaluationResponse> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseUrl}/parse-evaluation-components/`, {
        method: 'POST',
        body: formData,
        mode: 'cors', // Explicitly request CORS mode
        headers: {
          // Don't set Content-Type with FormData as browser will set it with boundary
          'Accept': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to parse PDF');
      }

      return await response.json();
    } catch (error) {
      console.error('Parse evaluation error:', error);
      throw error;
    }
  }

  /**
   * Convert API questions to local format
   */
  convertToLocalQuestions(apiQuestions: ApiQuestion[]): LocalQuestion[] {
    return apiQuestions.map(q => ({
      Content: q.content,
      Alternatives: q.alternatives,
      Evaluation: [],
      Type: q.type as "inputbox" | "slider" | "radio" | "yesno" // Explicitly cast to supported local types
    }));
  }

  /**
   * Calculates the total sum based on questions and responses
   */
  calculateTotalSum(
    questions: ApiQuestion[], 
    responses: Record<string, string | number>, 
    calculationOrder: string[]
  ): number {
    let baseValue = 0;
    let adjustments = 0;
    let percentMultiplier = 1;
    
    // Process in calculation order
    calculationOrder.forEach(questionId => {
      const question = questions.find(q => q.id === questionId);
      if (!question) return;
      
      const value = responses[question.id];
      if (value === undefined) return;
      
      const evaluation = question.evaluation;
      
      switch (evaluation.operation) {
        case "base":
          if (evaluation.valueType === "direct") {
            baseValue = typeof value === 'string' ? parseFloat(value) || 0 : value;
          }
          break;
          
        case "adjust":
          if (evaluation.valueType === "range" && evaluation.ranges) {
            const numValue = typeof value === 'string' ? parseFloat(value) || 0 : value;
            const range = evaluation.ranges.find(r => 
              numValue >= r.min && numValue <= r.max);
            if (range) adjustments += range.value;
          } 
          else if (evaluation.valueType === "map" && evaluation.mapping) {
            adjustments += evaluation.mapping[value as string] || 0;
          }
          break;
          
        case "percent":
          if (evaluation.valueType === "map" && evaluation.mapping) {
            percentMultiplier += evaluation.mapping[value as string] || 0;
          }
          break;
      }
    });
    
    return (baseValue + adjustments) * percentMultiplier;
  }

  /**
   * Get description for a question's adjustment based on the selected value
   */
  getAdjustmentDescription(question: ApiQuestion, value: string | number): string {
    const evaluation = question.evaluation;
    
    if (evaluation.operation === "adjust") {
      if (evaluation.valueType === "range" && evaluation.ranges) {
        const numValue = typeof value === 'string' ? parseFloat(value) || 0 : value;
        const range = evaluation.ranges.find(r => 
          numValue >= r.min && numValue <= r.max
        );
        if (range) {
          const amount = Math.abs(range.value).toLocaleString('sv-SE');
          return range.value > 0 
            ? `tillägg med ${amount} kr (+)`
            : `avdrag med ${amount} kr (-)`;
        }
      } 
      else if (evaluation.valueType === "map" && evaluation.mapping) {
        const adjValue = evaluation.mapping[value as string];
        if (adjValue !== undefined) {
          const amount = Math.abs(adjValue).toLocaleString('sv-SE');
          return adjValue > 0 
            ? `tillägg med ${amount} kr (+)`
            : `avdrag med ${amount} kr (-)`;
        }
      }
    }
    
    if (evaluation.operation === "percent" && evaluation.valueType === "map" && evaluation.mapping) {
      const percent = evaluation.mapping[value as string];
      if (percent !== undefined) {
        const percentText = Math.abs(percent * 100).toFixed(1);
        return percent > 0 
          ? `ökning med ${percentText}%`
          : `rabatt med ${percentText}%`;
      }
    }
    
    return "ingen justering";
  }

  /**
   * Format currency for display
   */
  formatCurrency(value: number): string {
    return value.toLocaleString('sv-SE') + ' kr';
  }
}
