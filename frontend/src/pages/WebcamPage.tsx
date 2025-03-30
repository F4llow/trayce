import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "@/components/Header";
import WebcamCapture from "@/components/WebcamCapture";
import { useToast } from "@/hooks/use-toast";
import { Loader } from "lucide-react";

const WebcamPage = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isLoading, setLoading] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const BACKEND_URL = "http://127.0.0.1:5000";

  const handleCapture = async () => {
    if (!canvasRef.current || !videoRef.current) return;

    // Draw the current video frame onto the canvas
    const canvas = canvasRef.current;
    const video = videoRef.current;
    const context = canvas.getContext("2d");
    if (context) {
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert the canvas content to a base64 image
      const imageSrc = canvas.toDataURL("image/jpeg");

      setLoading(true);
      try {
        // Send the base64 image to the Flask backend
        const response = await fetch(`${BACKEND_URL}/upload`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ image: imageSrc }),
        });

        if (!response.ok) {
          throw new Error("Failed to classify the image :(");
        }

        const data = await response.json();
        setLoading(false);

        navigate("/results", {
          state: {
            items: data.detections,
            image: data.image,
          },
        });
      } catch (error) {
        console.error("Error classifying image:", error);
        toast(
          "Oh no! There was a problem analyzing your image. Please try again."
        );
        setLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center p-6">
      <div className="max-w-md w-full">
        <Header
          title="Scan Your Tray"
          subtitle="Position all items clearly in the camera view."
        />

        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader className="h-12 w-12 text-primary animate-spin mb-4" />
            <p className="text-lg font-medium">Analyzing your tray items...</p>
            <p className="text-gray-500 mt-2">This may take a few moments.</p>
          </div>
        ) : (
          <WebcamCapture onCapture={handleCapture} />
        )}

        <div className="mt-8 text-center text-gray-600">
          <p>Ensure good lighting and that all items are clearly visible.</p>
        </div>
      </div>
    </div>
  );
};

export default WebcamPage;