import { Category, ClassifiedItem } from "@/types";

// Get appropriate category color
export const getCategoryColor = (category: Category): string => {
  switch (category) {
    case "trash":
      return "bg-gray-500";
    case "recycle":
      return "bg-blue-500";
    case "compost":
      return "bg-green-500";
    case "dish return":
      return "bg-yellow-500";
    default:
      return "bg-gray-500";
  }
};

// Get category icon name
export const getCategoryIcon = (category: Category): string => {
  switch (category) {
    case "trash":
      return "trash";
    case "recycle":
      return "recycle";
    case "compost":
      return "leaf";
    case "dish return":
      return "utensils";
    default:
      return "help-circle";
  }
};
