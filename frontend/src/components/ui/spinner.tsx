import { cn } from "@/lib/utils";
import { VariantProps, cva } from "class-variance-authority";
import { Loader2 } from "lucide-react";
import React from "react";

const spinnerVariants = cva("flex-col items-center justify-center rounded-full text-muted-foreground transition-all", {
    variants: {
        show: {
            true: "flex",
            false: "hidden",
        },
    },
    defaultVariants: {
        show: true,
    },
});

const loaderVariants = cva("animate-spin text-primary", {
    variants: {
        size: {
            sm: "h-4 w-4",
            md: "h-8 w-8",
            lg: "h-16 w-16",
            xl: "h-24 w-24",
            icon: "h-10 w-10",
        },
        variant: {
            light: "text-white",
            primary: "text-primary",
        },
    },
    defaultVariants: {
        size: "md",
        variant: "primary",
    },
});

interface SpinnerProps
    extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof spinnerVariants>,
    VariantProps<typeof loaderVariants> {
    className?: string;
    children?: React.ReactNode;
}

export function Spinner({ size, show, children, className, variant, ...props }: SpinnerProps) {
    return (
        <span className={spinnerVariants({ show })}>
            <Loader2 className={cn(loaderVariants({ size, variant }), className)} {...props} />
            {children}
        </span>
    );
}
