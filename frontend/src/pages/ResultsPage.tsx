import { useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { ClassifiedItem } from "@/types";
import Header from "@/components/Header";
import ItemsList from "@/components/ItemsList";
import { Button } from "@/components/ui/button";
import { getCategoryColor, getCategoryIcon } from "@/utils/classificationUtils";
import { RefreshCw } from "lucide-react";
import * as Icons from "lucide-react";

interface LocationState {
  items: ClassifiedItem[];
  image: string;
}

const ResultsPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { items, image } = (location.state as LocationState) || { items: [], image: "" };
  
  if (!items.length) {
    // Redirect to home if no items
    useEffect(() => {
      navigate("/");
    }, [navigate]);
    return null;
  }

  // Render icon based on category
  const renderIcon = (iconName: string) => {
    const LucideIcon = (Icons as any)[iconName === "recycle" ? "Recycle" : 
                                      iconName === "trash" ? "Trash" : 
                                      iconName === "leaf" ? "Leaf" : 
                                      iconName === "utensils" ? "Utensils" : "HelpCircle"];
    return <LucideIcon className="h-5 w-5" />;
  };
  
  return (
    <div className="min-h-screen flex flex-col items-center p-6">
      <div className="max-w-md w-full">
        <Header 
          title="Results" 
          subtitle={`${items.length} items identified`} 
        />
        
        <div className="mb-6">
          <div className="rounded-lg overflow-hidden border-2 border-primary mb-4">
            <img src={image} alt="Captured tray" className="w-full h-auto" />
          </div>
          
          <div className="space-y-4">
            {items.map((item) => (
              <div 
                key={item.id} 
                className="flex items-center border rounded-lg p-4 hover:shadow-md transition-shadow"
              >
                <div className={`${getCategoryColor(item.category)} p-3 rounded-full mr-4`}>
                  {renderIcon(getCategoryIcon(item.category))}
                </div>
                <div className="flex-1">
                  <h3 className="font-medium">{item.name}</h3>
                  <div className="flex items-center mt-1">
                    <span className="text-sm capitalize text-gray-600">{item.category}</span>
                    <span className="ml-auto text-sm text-gray-500">
                      {Math.round(item.confidence * 100)}% confidence
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-4">
          <ItemsList items={items} />
          
          <Button onClick={() => navigate("/")} className="flex-1">
            <RefreshCw className="mr-2 h-5 w-5" />
            Scan Again
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ResultsPage;