import React from "react";
import { ClassifiedItem } from "@/types";
import { getCategoryColor, getCategoryIcon } from "@/utils/classificationUtils";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { List } from "lucide-react";
import * as Icons from "lucide-react";

interface ItemsListProps {
  items: ClassifiedItem[];
}

const ItemsList: React.FC<ItemsListProps> = ({ items }) => {
  const groupedItems = items.reduce((acc, item) => {
    if (!acc[item.category]) {
      acc[item.category] = [];
    }
    acc[item.category].push(item);
    return acc;
  }, {} as Record<string, ClassifiedItem[]>);

  // Dynamically render the icon based on category
  const renderIcon = (iconName: string) => {
    const LucideIcon = (Icons as any)[iconName === "recycle" ? "Recycle" : 
                                      iconName === "trash" ? "Trash" : 
                                      iconName === "leaf" ? "Leaf" : 
                                      iconName === "utensils" ? "Utensils" : "HelpCircle"];
    return <LucideIcon className="h-5 w-5" />;
  };

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">
          <List className="mr-2 h-5 w-5" />
          View All Items
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Disposal Categories</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 mt-4">
          {Object.entries(groupedItems).map(([category, categoryItems]) => (
            <div key={category} className="border rounded-lg p-4">
              <div className={`flex items-center ${getCategoryColor(category as any)} text-white p-2 rounded-md mb-2`}>
                {renderIcon(getCategoryIcon(category as any))}
                <span className="ml-2 font-semibold capitalize">{category}</span>
              </div>
              <ul className="space-y-2">
                {categoryItems.map((item) => (
                  <li key={item.id} className="flex justify-between items-center">
                    <span>{item.name}</span>
                    <span className="text-sm text-gray-500">
                      {Math.round(item.confidence * 100)}% confidence
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default ItemsList;