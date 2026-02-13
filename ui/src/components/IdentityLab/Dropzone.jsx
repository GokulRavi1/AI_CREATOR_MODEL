import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload } from 'lucide-react';

export default function Dropzone({ onFileSelect }) {
    const onDrop = useCallback(acceptedFiles => {
        if (acceptedFiles?.length > 0) {
            onFileSelect(acceptedFiles[0]);
        }
    }, [onFileSelect]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'image/*': [] },
        multiple: false
    });

    return (
        <div
            {...getRootProps()}
            className={`dropzone ${isDragActive ? 'dragover' : ''}`}
        >
            <input {...getInputProps()} />
            <Upload className="dropzone-icon" strokeWidth={1.5} />
            <p className="dropzone-text">
                {isDragActive
                    ? "Drop the image here..."
                    : "Drag & drop control image, or click to select"}
            </p>
        </div>
    );
}
