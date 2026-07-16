"use client";

import * as React from "react";
import { Upload, FileSpreadsheet, Loader2 } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";

export default function ExcelAnalysisPage() {
  const [file, setFile] = React.useState<File | null>(null);
  const [analyzing, setAnalyzing] = React.useState(false);
  const [results, setResults] = React.useState<Record<string, unknown> | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setAnalyzing(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/documents/upload`,
        { method: "POST", body: formData, credentials: "include" }
      );
      if (!response.ok) throw new Error("Upload failed");
      const data = await response.json();
      setResults({ filename: file.name, status: "uploaded", id: data.id });
      toast.success("File uploaded. Your spreadsheet is ready for analysis.");
    } catch (err) {
      toast.error("Upload failed: " + String(err));
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Excel Analysis</h1>
        <p className="text-muted-foreground">Upload and analyze Excel spreadsheets</p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Upload Excel File</CardTitle>
          <CardDescription>Select an .xlsx or .xls file to analyze</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid w-full max-w-sm gap-1.5">
            <Label htmlFor="excel-file">Excel File</Label>
            <Input id="excel-file" type="file" accept=".xlsx,.xls" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
          </div>
          <Button onClick={handleUpload} disabled={!file || analyzing}>
            {analyzing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Upload className="mr-2 h-4 w-4" />}
            Upload & Analyze
          </Button>
          {results && (
            <div className="rounded-lg bg-muted p-4">
              <p className="font-medium">{results.filename as string}</p>
              <p className="text-sm text-muted-foreground">File uploaded successfully. Use the Data Analyst agent for in-depth analysis.</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
