// This file is the main page of the Next.js app. It demonstrates how to use React with TypeScript
// and interact with a FastAPI backend. UI components are from shadcn/ui.
"use client";

// Import UI components from shadcn/ui and Next.js's Image component
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Image from "next/image";
import { useState } from "react";

// The main React component for the home page
export default function Home() {
  // State for the input field
  const [input, setInput] = useState("");
  // State to store the response from the backend
  const [response, setResponse] = useState<string | null>(null);
  // State to indicate if a request is in progress
  const [loading, setLoading] = useState(false);
  // State to store any error message
  const [error, setError] = useState<string | null>(null);

  // This function handles the form submission.
  // It sends a POST request to the FastAPI backend and updates state based on the response.
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // Prevent the default form submission behavior
    setLoading(true); // Show loading state
    setError(null); // Clear previous errors
    setResponse(null); // Clear previous response
    try {
      // Send a POST request to the FastAPI backend
      const res = await fetch("http://localhost:8000/echo", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        // Send the input as JSON in the request body
        body: JSON.stringify({ message: input }),
      });
      if (!res.ok) throw new Error("Request failed"); // Handle HTTP errors
      const data = await res.json(); // Parse the JSON response
      setResponse(data.message); // Update the response state
    } catch (err: unknown) {
      // Handle errors (network or parsing)
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Unknown error");
      }
    } finally {
      setLoading(false); // Always stop loading
    }
  };

  return (
    // The main container uses Tailwind CSS for layout and background
    <div className="font-sans grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 bg-gradient-to-br from-slate-100 to-slate-300 dark:from-[#18181b] dark:to-[#23272f]">
      {/* Main content area */}
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start w-full max-w-xl">
        {/* Page title */}
        <h1 className="text-3xl font-bold tracking-tight text-center w-full mb-2 text-slate-900 dark:text-slate-100">
          nextjs-fastapi
        </h1>
        {/* Card component for the echo form */}
        <Card className="w-full max-w-xl">
          <CardHeader>
            <CardTitle>Echo Message</CardTitle>
          </CardHeader>
          <CardContent>
            {/* Form to send a message to the backend */}
            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
              {/* Label for the input field */}
              <Label htmlFor="echo-input">Type your message</Label>
              {/* Input field for user message */}
              <Input
                id="echo-input"
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)} // Update input state on change
                placeholder="Type your message..."
                disabled={loading}
                required
                className="text-base"
              />
              {/* Submit button, disabled if loading or input is empty */}
              <Button
                type="submit"
                disabled={loading || !input.trim()}
                className="mt-2"
              >
                {loading ? "Sending..." : "Send"}
              </Button>
              {/* Show the response from the backend if available */}
              {response && (
                <div className="mt-2 text-green-700 dark:text-green-400 font-mono text-base rounded bg-green-100 dark:bg-green-900/30 px-3 py-2">
                  {response}
                </div>
              )}
              {/* Show error message if there was an error */}
              {error && (
                <div className="mt-2 text-red-600 dark:text-red-400 font-mono text-base rounded bg-red-100 dark:bg-red-900/30 px-3 py-2">
                  {error}
                </div>
              )}
            </form>
          </CardContent>
        </Card>
      </main>
      {/* Footer with resource links */}
      <footer className="row-start-3 flex gap-[24px] flex-wrap items-center justify-center">
        {/* Link to shadcn/ui documentation */}
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://ui.shadcn.com/docs"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/file.svg"
            alt="File icon"
            width={16}
            height={16}
          />
          shadcn/ui Docs
        </a>
        {/* Link to shadcn/ui GitHub repo */}
        <a
          className="flex items-center gap-2 hover:underline hover:underline-offset-4"
          href="https://github.com/shadcn/ui"
          target="_blank"
          rel="noopener noreferrer"
        >
          <Image
            aria-hidden
            src="/window.svg"
            alt="Window icon"
            width={16}
            height={16}
          />
          shadcn/ui GitHub
        </a>
      </footer>
    </div>
  );
}
