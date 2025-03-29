export type Category = 'trash' | 'recycle' | 'compost' | 'dish return';

export interface ClassifiedItem {
  id: string;
  name: string;
  category: Category;
  confidence: number;
}
