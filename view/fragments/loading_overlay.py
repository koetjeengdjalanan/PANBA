"""Loading overlay fragment.

Usage:
    from view.fragments.loading_overlay import load_overlay

    with load_overlay(master=some_frame, text="Working...") as lo:
        # perform tasks (ideally in a worker thread if long-running)
        ...

Notes:
    This overlay is meant for short synchronous tasks. If the code inside the
    context blocks the Tk mainloop for a long time, the animation will freeze.
    For long tasks, run them in a separate thread and then join inside the
    context or explicitly call `lo.pulse()` periodically.
"""

from __future__ import annotations

import threading
from typing import Any, Callable, Optional, Union

try:  # CustomTkinter is the UI framework used in the project
    import customtkinter as ctk
except ImportError as e:  # pragma: no cover - defensive
    raise RuntimeError("customtkinter must be installed to use loading overlay") from e


class LoadingOverlay:
    """Context manager that shows a semi-opaque overlay with a spinner/progress bar.

    Parameters
    ----------
    master: ctk.CTkBaseClass
        Parent container (Frame / Toplevel / root) to cover.
    text: str
        Message displayed under the spinner.
    cancelable: bool
        If True, shows a cancel button and allows user cancel via callback.
    on_cancel: Callable[[], None] | None
        Callback executed if user presses the cancel button.
    block_events: bool
        If True (default) the overlay captures clicks so underlying widgets
        are effectively disabled while shown.
    use_toplevel: bool
        If True, uses a borderless transient toplevel instead of an in-place frame.
        (A toplevel can appear above other widgets more reliably.)
    """

    def __init__(
        self,
        master: "ctk.CTkBaseClass",
        *,
        text: str = "Loading...",
        cancelable: bool = False,
        on_cancel: Optional[Callable[[], None]] = None,
        block_events: bool = True,
        use_toplevel: bool = False,
    ) -> None:
        self.master = master
        self.text_value = text
        self.cancelable = cancelable
        self.on_cancel = on_cancel
        self.block_events = block_events
        self.use_toplevel = use_toplevel

        self._overlay: Optional[Union[ctk.CTkFrame, ctk.CTkToplevel]] = None
        self._label: Optional[ctk.CTkLabel] = None
        self._progress: Optional[ctk.CTkProgressBar] = None
        self._cancel_btn: Optional[ctk.CTkButton] = None
        self._running = False
        self._spinner_thread: Optional[threading.Thread] = None

    # ---------------------------------------------------------------------
    # Construction
    # ---------------------------------------------------------------------
    def _build(self) -> None:
        parent = self.master
        parent.update_idletasks()

        if self.use_toplevel:
            ov = ctk.CTkToplevel(parent)
            ov.overrideredirect(True)
            ov.transient(parent.winfo_toplevel())
            # Position to exactly cover parent
            x = parent.winfo_rootx()
            y = parent.winfo_rooty()
            w = parent.winfo_width()
            h = parent.winfo_height()
            ov.geometry(f"{w}x{h}+{x}+{y}")
            ov.lift()
            ov.attributes("-topmost", True)
        else:
            ov = ctk.CTkFrame(parent, corner_radius=0, fg_color=("transparent"))
            # ov = ctk.CTkFrame(parent, corner_radius=0, fg_color=("#222222", "#222222"))
            ov.place(relx=0, rely=0, relwidth=1, relheight=1)
            ov.lift()

        # Content container (centered)
        inner = ctk.CTkFrame(ov, corner_radius=8, fg_color=("gray90", "gray15"))
        inner.pack(expand=True)
        inner.pack_propagate(False)
        inner.configure(width=260, height=140)

        lbl = ctk.CTkLabel(inner, text=self.text_value, wraplength=240, justify="center")
        lbl.pack(padx=20, pady=(25, 10))
        self._label = lbl

        pb = ctk.CTkProgressBar(inner, mode="indeterminate")
        pb.pack(fill="x", padx=25, pady=(0, 12))
        pb.start()
        self._progress = pb

        if self.cancelable:
            self._cancel_btn = ctk.CTkButton(
                inner,
                text="Cancel",
                command=self._handle_cancel,
                width=100,
            )
            self._cancel_btn.pack(pady=(0, 16))

        # Capture events to block underlying widgets if requested
        if self.block_events:

            def swallow(event: Any) -> str:
                return "break"

            for seq in ("<Button-1>", "<Button-2>", "<Button-3>", "<Key>"):
                ov.bind(seq, swallow)

        self._overlay = ov
        self._running = True

        if self.use_toplevel:
            # Periodically realign to parent in case of resize/move
            self._schedule_reposition()

    def _schedule_reposition(self):
        if not self._running or not self.use_toplevel or self._overlay is None:
            return
        parent = self.master
        ov = self._overlay
        try:
            x = parent.winfo_rootx()
            y = parent.winfo_rooty()
            w = parent.winfo_width()
            h = parent.winfo_height()
            ov.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:  # pragma: no cover
            pass
        finally:
            parent.after(300, self._schedule_reposition)

    # ------------------------------------------------------------------
    # API
    # ------------------------------------------------------------------
    def update_text(self, text: str) -> None:
        """Update the message text displayed in the overlay."""
        self.text_value = text
        if self._label is not None:
            self._label.configure(text=text)
            self._label.update_idletasks()

    def pulse(self) -> None:
        """Force a UI update (useful if blocking mainloop)."""
        if self._overlay is not None:
            self._overlay.update_idletasks()
            self._overlay.update()

    def _handle_cancel(self):
        if self.on_cancel:
            try:
                self.on_cancel()
            finally:
                self.close()
        else:
            self.close()

    def close(self) -> None:
        """Close and destroy the overlay if it is currently shown."""
        if not self._running:
            return
        self._running = False
        try:
            if self._progress is not None:
                try:
                    self._progress.stop()
                except Exception:  # pragma: no cover
                    pass
            if self._overlay is not None:
                if self.use_toplevel:
                    self._overlay.destroy()
                else:
                    self._overlay.place_forget()
                    self._overlay.destroy()
        finally:
            self._overlay = None

    # ------------------------------------------------------------------
    # Context manager interface
    # ------------------------------------------------------------------
    def __enter__(self) -> "LoadingOverlay":
        """Enter the context, build & show the overlay, and return self."""
        self._build()
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        """Exit the context and always remove the overlay.

        Returning False to propagate any exception that occurred inside.
        """
        # Always close overlay
        self.close()
        # Propagate exception (return False)
        return False


def load_overlay(**kwargs: Any) -> LoadingOverlay:
    """Factory returning a context-manageable loading overlay.

    Example:
        with load_overlay(master=frame, text="Fetching data...") as ov:
            do_work()
            ov.update_text("Almost done...")

    Accepts the same keyword arguments as LoadingOverlay.
    """
    if "master" not in kwargs:
        raise ValueError("master parameter is required for load_overlay()")
    return LoadingOverlay(**kwargs)


__all__ = ["LoadingOverlay", "load_overlay"]
