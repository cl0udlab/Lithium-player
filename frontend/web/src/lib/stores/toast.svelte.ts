import { Toaster } from 'melt/builders'

export type ToastKind = 'success' | 'error' | 'info'

export interface ToastData {
	kind: ToastKind
	title: string
	description?: string
}

export const toaster = new Toaster<ToastData>({ closeDelay: 4000, hover: 'pause' })

function add(kind: ToastKind, title: string, description?: string) {
	toaster.addToast({ data: { kind, title, description } })
}

export const toast = {
	success: (title: string, description?: string) => add('success', title, description),
	error: (title: string, description?: string) => add('error', title, description),
	info: (title: string, description?: string) => add('info', title, description)
}
