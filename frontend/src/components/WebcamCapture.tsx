
import React, { useRef, useCallback, useState } from "react";
import Webcam from "react-webcam";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Camera, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface WebcamCaptureProps {
  onCapture: (imageSrc: string) => void;
}

const WebcamCapture: React.FC<WebcamCaptureProps> = ({ onCapture }) => {
  const navigate = useNavigate(); // Initialize useNavigate
  const webcamRef = useRef<Webcam>(null);
  const [isCameraReady, setIsCameraReady] = useState(false);
  const [facingMode, setFacingMode] = useState<"user" | "environment">("environment");
  const BACKEND_URL = "http://127.0.0.1:5000";

  const handleCapture = useCallback(async () => {
    const imageSrc = webcamRef.current?.getScreenshot();

    if (imageSrc) {
      try {
        console.log("Captured image:", imageSrc); // Debugging
  
        // Send the captured image to the backend with custom headers
        const response = await axios.post(
          `${BACKEND_URL}/upload`,
          { image: imageSrc },
          {
            headers: {
              "Content-Type": "application/json", // Content type is JSON
              // "Authorization": "Bearer YOUR_TOKEN_HERE", // 
            },
          }
        );
  
        console.log("Backend response:", response.data); // Debugging
        const { result } = response.data;

        // Pass the backend result to the onCapture callback
        onCapture(result);

        // Navigate to the results page with the result as state
        navigate("/results", { state: { result } });
      } catch (error) {
        console.error("Error sending image to backend:", error);
        onCapture("Error: Unable to catalogue image.");
      }
    }
  }, [webcamRef, onCapture]);

  const toggleCamera = () => {
    setFacingMode(prev => prev === "user" ? "environment" : "user");
  };

  const videoConstraints = {
    facingMode: facingMode,
    width: { min: 640 },
    height: { min: 480 }
  };

  return (
    <div className="flex flex-col items-center">
      <div className="relative mb-4 w-full max-w-md overflow-hidden rounded-lg border-2 border-primary">
        <Webcam
          audio={false}
          ref={webcamRef}
          screenshotFormat="image/jpeg"
          videoConstraints={videoConstraints}
          onUserMedia={() => setIsCameraReady(true)}
          className="w-full h-auto"
        />
        <Button 
          variant="outline" 
          size="icon" 
          className="absolute bottom-2 right-2"
          onClick={toggleCamera}
        >
          <RefreshCw className="h-5 w-5" />
        </Button>
      </div>

      <Button 
        onClick={handleCapture} 
        disabled={!isCameraReady}
        className="w-full max-w-md mt-2 text-gray-800"
      >
        <Camera className="mr-2 h-5 w-5" />
        Capture Image
      </Button>
    </div>
  );
};

export default WebcamCapture;