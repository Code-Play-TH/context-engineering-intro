"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ArrowLeft, Upload, FileText, CheckCircle, XCircle, AlertCircle, Download } from "lucide-react";
import { useUploadKOLImport, useValidateKOLImport, useProcessKOLImport, useKOLImportStatus } from "@/hooks/useKOLs";

export default function KOLImportPage() {
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);

    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [currentJobId, setCurrentJobId] = useState<number | null>(null);
    const [step, setStep] = useState<'upload' | 'validate' | 'process' | 'complete'>('upload');

    const uploadImport = useUploadKOLImport();
    const validateImport = useValidateKOLImport();
    const processImport = useProcessKOLImport();
    const { data: importStatus } = useKOLImportStatus(currentJobId);

    const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (file) {
            // Validate file type
            const allowedTypes = ['.csv', '.xlsx', '.xls'];
            const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();

            if (!allowedTypes.includes(fileExtension)) {
                alert('Please select a CSV or Excel file (.csv, .xlsx, .xls)');
                return;
            }

            // Validate file size (50MB max)
            if (file.size > 50 * 1024 * 1024) {
                alert('File size must be less than 50MB');
                return;
            }

            setSelectedFile(file);
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        try {
            const job = await uploadImport.mutateAsync(selectedFile);
            setCurrentJobId(job.id);
            setStep('validate');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to upload file');
        }
    };

    const handleValidate = async () => {
        if (!currentJobId) return;

        try {
            await validateImport.mutateAsync(currentJobId);
            setStep('process');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to validate import');
        }
    };

    const handleProcess = async () => {
        if (!currentJobId) return;

        try {
            await processImport.mutateAsync(currentJobId);
            setStep('complete');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Failed to process import');
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="h-5 w-5 text-green-500" />;
            case 'failed':
                return <XCircle className="h-5 w-5 text-red-500" />;
            case 'pending':
            case 'validating':
            case 'processing':
                return <AlertCircle className="h-5 w-5 text-yellow-500" />;
            default:
                return <FileText className="h-5 w-5 text-gray-500" />;
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800';
            case 'failed':
                return 'bg-red-100 text-red-800';
            case 'pending':
            case 'validating':
            case 'processing':
                return 'bg-yellow-100 text-yellow-800';
            default:
                return 'bg-gray-100 text-gray-800';
        }
    };

    const downloadSampleCSV = () => {
        const sampleData = [
            ['name', 'email', 'phone', 'location', 'niche', 'tags', 'notes', 'instagram_handle', 'instagram_followers', 'tiktok_handle', 'tiktok_followers', 'youtube_handle', 'youtube_followers'],
            ['John Influencer', 'john@example.com', '+1234567890', 'Bangkok, Thailand', 'fashion,lifestyle', 'micro-influencer,fashion', 'Great engagement rate', '@johnfashion', '50000', '@johntiktok', '25000', 'JohnYouTube', '10000'],
            ['Jane Creator', 'jane@example.com', '', 'Singapore', 'beauty,skincare', 'beauty-guru', 'Specializes in skincare reviews', '@janebeauty', '75000', '', '', '', ''],
        ];

        const csvContent = sampleData.map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'kol_import_sample.csv';
        a.click();
        window.URL.revokeObjectURL(url);
    };

    return (
        <DashboardLayout>
            <div className="max-w-4xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => router.back()}>
                        <ArrowLeft className="h-5 w-5" />
                    </Button>
                    <div>
                        <h1 className="text-3xl font-bold">Import KOLs</h1>
                        <p className="text-muted-foreground">
                            Upload a CSV or Excel file to import multiple KOLs at once
                        </p>
                    </div>
                </div>

                {/* Progress Steps */}
                <Card>
                    <CardContent className="pt-6">
                        <div className="flex items-center justify-between">
                            <div className={`flex items-center gap-2 ${step === 'upload' ? 'text-primary' : step !== 'upload' ? 'text-green-600' : 'text-muted-foreground'}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'upload' ? 'bg-primary text-white' : step !== 'upload' ? 'bg-green-100 text-green-600' : 'bg-gray-100'}`}>
                                    1
                                </div>
                                <span className="font-medium">Upload File</span>
                            </div>
                            <div className={`flex items-center gap-2 ${step === 'validate' ? 'text-primary' : ['process', 'complete'].includes(step) ? 'text-green-600' : 'text-muted-foreground'}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'validate' ? 'bg-primary text-white' : ['process', 'complete'].includes(step) ? 'bg-green-100 text-green-600' : 'bg-gray-100'}`}>
                                    2
                                </div>
                                <span className="font-medium">Validate Data</span>
                            </div>
                            <div className={`flex items-center gap-2 ${step === 'process' ? 'text-primary' : step === 'complete' ? 'text-green-600' : 'text-muted-foreground'}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'process' ? 'bg-primary text-white' : step === 'complete' ? 'bg-green-100 text-green-600' : 'bg-gray-100'}`}>
                                    3
                                </div>
                                <span className="font-medium">Process Import</span>
                            </div>
                            <div className={`flex items-center gap-2 ${step === 'complete' ? 'text-green-600' : 'text-muted-foreground'}`}>
                                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${step === 'complete' ? 'bg-green-100 text-green-600' : 'bg-gray-100'}`}>
                                    ✓
                                </div>
                                <span className="font-medium">Complete</span>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                {/* Step 1: Upload File */}
                {step === 'upload' && (
                    <Card>
                        <CardHeader>
                            <CardTitle>Upload CSV or Excel File</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            {/* Sample Download */}
                            <div className="bg-blue-50 p-4 rounded-lg">
                                <div className="flex items-start gap-3">
                                    <FileText className="h-5 w-5 text-blue-600 mt-0.5" />
                                    <div className="flex-1">
                                        <h3 className="font-medium text-blue-900">Need a template?</h3>
                                        <p className="text-sm text-blue-700 mt-1">
                                            Download our sample CSV file to see the expected format and required columns.
                                        </p>
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="mt-2"
                                            onClick={downloadSampleCSV}
                                        >
                                            <Download className="h-4 w-4 mr-2" />
                                            Download Sample CSV
                                        </Button>
                                    </div>
                                </div>
                            </div>

                            {/* File Upload */}
                            <div className="space-y-4">
                                <div
                                    className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary transition-colors"
                                    onClick={() => fileInputRef.current?.click()}
                                >
                                    <Upload className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                                    <p className="text-lg font-medium mb-2">
                                        {selectedFile ? selectedFile.name : 'Click to upload file'}
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        Supports CSV, XLSX, and XLS files up to 50MB
                                    </p>
                                </div>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept=".csv,.xlsx,.xls"
                                    onChange={handleFileSelect}
                                    className="hidden"
                                />
                            </div>

                            {selectedFile && (
                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <p className="font-medium">{selectedFile.name}</p>
                                            <p className="text-sm text-muted-foreground">
                                                {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                            </p>
                                        </div>
                                        <Button onClick={handleUpload} disabled={uploadImport.isPending}>
                                            {uploadImport.isPending ? 'Uploading...' : 'Upload & Continue'}
                                        </Button>
                                    </div>
                                </div>
                            )}

                            {/* Required Columns Info */}
                            <div className="space-y-4">
                                <h3 className="font-medium">Required Columns</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                                    <div>
                                        <h4 className="font-medium text-green-600">Required</h4>
                                        <ul className="mt-2 space-y-1 text-muted-foreground">
                                            <li>• name</li>
                                            <li>• At least one social media handle</li>
                                        </ul>
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-blue-600">Optional</h4>
                                        <ul className="mt-2 space-y-1 text-muted-foreground">
                                            <li>• email, phone, location</li>
                                            <li>• niche (comma-separated)</li>
                                            <li>• tags (comma-separated)</li>
                                            <li>• notes</li>
                                            <li>• Social handles: instagram_handle, tiktok_handle, etc.</li>
                                            <li>• Follower counts: instagram_followers, tiktok_followers, etc.</li>
                                        </ul>
                                    </div>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Step 2: Validate Data */}
                {step === 'validate' && importStatus && (
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-3">
                                <CardTitle>Validate Import Data</CardTitle>
                                {getStatusIcon(importStatus.status)}
                                <Badge className={getStatusColor(importStatus.status)}>
                                    {importStatus.status}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-3 gap-4 text-center">
                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <p className="text-2xl font-bold">{importStatus.total_rows}</p>
                                    <p className="text-sm text-muted-foreground">Total Rows</p>
                                </div>
                                <div className="p-4 bg-green-50 rounded-lg">
                                    <p className="text-2xl font-bold text-green-600">{importStatus.success_count || 0}</p>
                                    <p className="text-sm text-muted-foreground">Valid Rows</p>
                                </div>
                                <div className="p-4 bg-red-50 rounded-lg">
                                    <p className="text-2xl font-bold text-red-600">{importStatus.error_count || 0}</p>
                                    <p className="text-sm text-muted-foreground">Errors</p>
                                </div>
                            </div>

                            {importStatus.errors && importStatus.errors.length > 0 && (
                                <div className="space-y-2">
                                    <h4 className="font-medium text-red-600">Validation Errors</h4>
                                    <div className="max-h-40 overflow-y-auto space-y-1">
                                        {importStatus.errors.slice(0, 10).map((error, index) => (
                                            <div key={index} className="text-sm p-2 bg-red-50 rounded text-red-700">
                                                Row {error.row}: {error.message}
                                            </div>
                                        ))}
                                        {importStatus.errors.length > 10 && (
                                            <p className="text-sm text-muted-foreground">
                                                ... and {importStatus.errors.length - 10} more errors
                                            </p>
                                        )}
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-2">
                                {importStatus.status === 'pending' && (
                                    <Button onClick={handleValidate} disabled={validateImport.isPending}>
                                        {validateImport.isPending ? 'Validating...' : 'Start Validation'}
                                    </Button>
                                )}
                                {importStatus.status === 'completed' && importStatus.error_count === 0 && (
                                    <Button onClick={() => setStep('process')}>
                                        Continue to Import
                                    </Button>
                                )}
                                {importStatus.status === 'failed' && (
                                    <Button variant="outline" onClick={() => setStep('upload')}>
                                        Upload New File
                                    </Button>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Step 3: Process Import */}
                {step === 'process' && importStatus && (
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-3">
                                <CardTitle>Process Import</CardTitle>
                                {getStatusIcon(importStatus.status)}
                                <Badge className={getStatusColor(importStatus.status)}>
                                    {importStatus.status}
                                </Badge>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-2 gap-4 text-center">
                                <div className="p-4 bg-blue-50 rounded-lg">
                                    <p className="text-2xl font-bold text-blue-600">{importStatus.processed_rows}</p>
                                    <p className="text-sm text-muted-foreground">Processed</p>
                                </div>
                                <div className="p-4 bg-green-50 rounded-lg">
                                    <p className="text-2xl font-bold text-green-600">{importStatus.success_count}</p>
                                    <p className="text-sm text-muted-foreground">Imported</p>
                                </div>
                            </div>

                            {importStatus.status === 'processing' && (
                                <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                        <span>Progress</span>
                                        <span>{Math.round((importStatus.processed_rows / importStatus.total_rows) * 100)}%</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className="bg-primary h-2 rounded-full transition-all duration-300"
                                            style={{ width: `${(importStatus.processed_rows / importStatus.total_rows) * 100}%` }}
                                        />
                                    </div>
                                </div>
                            )}

                            <div className="flex gap-2">
                                {importStatus.status === 'pending' && (
                                    <Button onClick={handleProcess} disabled={processImport.isPending}>
                                        {processImport.isPending ? 'Starting...' : 'Start Import'}
                                    </Button>
                                )}
                                {importStatus.status === 'completed' && (
                                    <Button onClick={() => setStep('complete')}>
                                        View Results
                                    </Button>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                )}

                {/* Step 4: Complete */}
                {step === 'complete' && importStatus && (
                    <Card>
                        <CardHeader>
                            <div className="flex items-center gap-3">
                                <CheckCircle className="h-6 w-6 text-green-500" />
                                <CardTitle className="text-green-600">Import Complete!</CardTitle>
                            </div>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-3 gap-4 text-center">
                                <div className="p-4 bg-gray-50 rounded-lg">
                                    <p className="text-2xl font-bold">{importStatus.total_rows}</p>
                                    <p className="text-sm text-muted-foreground">Total Rows</p>
                                </div>
                                <div className="p-4 bg-green-50 rounded-lg">
                                    <p className="text-2xl font-bold text-green-600">{importStatus.success_count}</p>
                                    <p className="text-sm text-muted-foreground">Successfully Imported</p>
                                </div>
                                <div className="p-4 bg-red-50 rounded-lg">
                                    <p className="text-2xl font-bold text-red-600">{importStatus.error_count}</p>
                                    <p className="text-sm text-muted-foreground">Failed</p>
                                </div>
                            </div>

                            <div className="flex gap-2">
                                <Button onClick={() => router.push('/kols')}>
                                    View KOL Database
                                </Button>
                                <Button variant="outline" onClick={() => {
                                    setStep('upload');
                                    setSelectedFile(null);
                                    setCurrentJobId(null);
                                }}>
                                    Import Another File
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                )}
            </div>
        </DashboardLayout>
    );
}