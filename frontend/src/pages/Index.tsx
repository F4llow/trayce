import React from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom'
import { Camera, Trash2, Recycle, Leaf, UtensilsCrossed } from 'lucide-react';
import Header from '@/components/Header';

const Index = () => {
    const navigate = useNavigate();
    
    return (
        <div className="min-h-screen flex flex-col items-center justify-center p-6">
        <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
          <Header 
            title="Traycer" 
            subtitle="Use computer vision for sustainable waste management" 
          />
          
          <div className="mb-8 text-center">
            <p className="text-gray-600">
              This tool helps you identify how to properly dispose of items on your food tray.
              Simply take a photo and our AI will classify each item into the right category.
            </p>
            
            <div className="grid grid-cols-2 gap-4 mt-6">
              <div className="flex flex-col items-center p-3 rounded-lg hover:shadow-lg transform transition-transform hover:scale-105 bg-gray-500 text-white">
                <div className="p-2 rounded-full mb-2">
                  <Trash2 className="block h-6 w-6" />
                </div>
                <span className="text-sm font-medium">Trash</span>
              </div>
              <div className="flex flex-col items-center p-3 rounded-lg hover:shadow-lg transform transition-transform hover:scale-105 bg-blue-500 text-white">
                <div className="p-2 rounded-full mb-2">
                  <Recycle className="block h-6 w-6" />
                </div>
                <span className="text-sm font-medium">Recycle</span>
              </div>
              <div className="flex flex-col items-center p-3 rounded-lg hover:shadow-lg transform transition-transform hover:scale-105 bg-green-500 text-white">
                <div className="p-2 rounded-full mb-2">
                  <Leaf className="block h-6 w-6" />
                </div>
                <span className="text-sm font-medium">Compost</span>
              </div>
              <div className="flex flex-col items-center p-3 rounded-lg hover:shadow-lg transform transition-transform hover:scale-105 bg-yellow-500 text-white">
                <div className="p-2 rounded-full mb-2">
                  <UtensilsCrossed className="block h-6 w-6" />
                </div>
                <span className="text-sm font-medium">Dish Return</span>
              </div>
            </div>
          </div>
          
          <Button
            onClick={() => navigate("/webcam")}
            className="w-full py-6 text-lg"
          >
            <Camera className="mr-2 h-6 w-6 text-gray-800" />
            Start Scanning
          </Button>
        </div>
      </div>
    );
};

export default Index;