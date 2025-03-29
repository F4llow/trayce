import toast, { Toaster, ToastOptions } from "react-hot-toast"

export function useToast() {
  const showToast = (message: string, options?: ToastOptions) => {
    toast(message, options)
  }

  const dismissToast = (toastId?: string) => {
    toast.dismiss(toastId)
  }

  return {
    toast: showToast,
    dismiss: dismissToast,
    ToasterComponent: Toaster, // Use this in your app to render the toast container
  }
}