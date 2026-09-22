import customtkinter as ctk

# Paleta hover coherente (usada en toda la app)
HOVER_LIGHTEN = {
    "#7C3AED": "#8B5CF6",  # primario -> más claro
    "#6D28D9": "#7C3AED",
    "#3D1559": "#4E1D70",
    "#22C55E": "#4ADE80",
    "#DC2626": "#EF4444",
    "gray": "#6B7280",
    "#d9534f": "#e57373",
}

def _hex_lighten(hex_color: str, amount: int = 20) -> str:
    """Aclara un color hex para hover (sin dependencias)."""
    try:
        hex_color = hex_color.lstrip("#")
        r = min(255, int(hex_color[0:2], 16) + amount)
        g = min(255, int(hex_color[2:4], 16) + amount)
        b = min(255, int(hex_color[4:6], 16) + amount)
        return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        return hex_color

def crear_boton_interactivo(parent, text, command, fg_color="#7C3AED", width=120, height=32, **kwargs):
    """CTkButton con hover visible, cursor mano y feedback pressed."""
    hover = kwargs.pop("hover_color", None)
    if hover is None:
        hover = HOVER_LIGHTEN.get(fg_color, _hex_lighten(fg_color, 22))
    btn = ctk.CTkButton(
        parent, text=text, command=command,
        fg_color=fg_color, hover_color=hover,
        width=width, height=height,
        corner_radius=8,
        **kwargs
    )
    # cursor mano + feedback pressed (ligero scale visual)
    try:
        btn.bind("<Enter>", lambda e: btn.configure(cursor="hand2"))
        btn.bind("<Leave>", lambda e: btn.configure(cursor=""))
        # pressed effect: oscurece levemente
        btn.bind("<ButtonPress-1>", lambda e: btn.configure(fg_color=hover))
        btn.bind("<ButtonRelease-1>", lambda e: btn.configure(fg_color=fg_color))
    except Exception:
        pass
    return btn


def crear_card_interactiva(parent, hover_bg="#F3E8FF", border_hover="#DDD6E5"):
    """Card blanca estilo Configuración.

    NOTA: sin cambio de color en hover a propósito — reconfigurar fg_color
    en cada <Enter>/<Leave> (y propagado a hijos) causa parpadeo/tintineo
    constante al mover el mouse sobre listas largas. Solo cursor mano.
    Se mantiene la firma por compatibilidad.
    """
    frame = ctk.CTkFrame(parent, fg_color="white", border_width=1, border_color="#E5E7EB",
                         corner_radius=8)
    try:
        frame.bind("<Enter>", lambda e: frame.configure(cursor="hand2"))
        frame.bind("<Leave>", lambda e: frame.configure(cursor=""))
    except Exception:
        pass
    return frame


# ── Estándar estilo Configuración (todas las vistas lista) ──
TITULO_COLOR = "#3D1559"
DESC_COLOR = "#6B5B7B"

def crear_seccion(parent, titulo, icono="", descripcion="", nro=None, badge=None):
    """Sección blanca estilo Configuración: head con nro+icono+título + badge + descripción."""
    sec = ctk.CTkFrame(parent, fg_color="white", corner_radius=8)
    sec.pack(fill="x", padx=5, pady=5)
    head = ctk.CTkFrame(sec, fg_color="transparent")
    head.pack(fill="x", padx=10, pady=(8, 4))
    pref = f"{nro}. " if nro is not None else ""
    ctk.CTkLabel(head, text=f"{pref}{icono}  {titulo}" if icono else f"{pref}{titulo}",
                 font=ctk.CTkFont(size=14, weight="bold"), text_color=TITULO_COLOR).pack(side="left")
    if badge:
        ctk.CTkLabel(head, text=badge, font=ctk.CTkFont(size=10), text_color="white",
                     fg_color="#7C3AED", corner_radius=6, width=50).pack(side="right")
    if descripcion:
        ctk.CTkLabel(sec, text=descripcion, font=ctk.CTkFont(size=11), text_color=DESC_COLOR,
                     justify="left", wraplength=650).pack(anchor="w", padx=10, pady=(0, 6))
    return sec


def crear_nota(parent, texto):
    """Nota ℹ gris estilo Configuración."""
    lbl = ctk.CTkLabel(parent, text=f"ℹ {texto}", font=ctk.CTkFont(size=11),
                       text_color=DESC_COLOR, justify="left", wraplength=620)
    lbl.pack(anchor="w", padx=10, pady=2)
    return lbl


COLORES_SEVERIDAD = {
    "alta": ("#FDE8E8", "#DC2626"),
    "media": ("#FEF3E2", "#D97706"),
    "info": ("#F3E8FF", "#7C3AED"),
}


def crear_banner_avisos(parent, texto, cantidad=None, severidad="media", command=None):
    """Fase 1: chip de aviso por módulo (sin toast). Si hay command, es clickeable."""
    fondo, borde = COLORES_SEVERIDAD.get(severidad, COLORES_SEVERIDAD["media"])
    marco = ctk.CTkFrame(parent, fg_color=fondo, corner_radius=8,
                         border_width=1, border_color=borde)
    marco.pack(fill="x", padx=8, pady=4)
    icono = {"alta": "🔴", "media": "🟠", "info": "🟣"}.get(severidad, "🟠")
    txt = f"{icono} {texto}" if cantidad is None else f"{icono} {texto} ({cantidad})"
    lbl = ctk.CTkLabel(marco, text=txt, font=ctk.CTkFont(size=12, weight="bold"),
                       text_color=borde)
    lbl.pack(side="left", padx=10, pady=8)
    if command is not None:
        btn = ctk.CTkButton(marco, text="Ver", width=80, height=28,
                            fg_color=borde, hover_color=borde, command=command)
        btn.pack(side="right", padx=10, pady=6)
        try:
            marco.configure(cursor="hand2")
            lbl.configure(cursor="hand2")
            marco.bind("<Button-1>", lambda e: command(), add="+")
            lbl.bind("<Button-1>", lambda e: command(), add="+")
        except Exception:
            pass
    return marco


def mostrar_cargando(parent, texto="Cargando"):
    """Indicador flotante con puntos animados. Retorna detener() que lo quita.

    Uso: overlay, detener = mostrar_cargando(frame); frame.update_idletasks();
    ... trabajo pesado ...; detener(). Seguro si el padre ya no existe.
    """
    try:
        lbl = ctk.CTkLabel(parent, text=f"⏳ {texto}",
                           font=ctk.CTkFont(size=15, weight="bold"),
                           text_color=TITULO_COLOR, fg_color="white",
                           corner_radius=8)
        lbl.place(relx=0.5, rely=0.5, anchor="center")
    except Exception:
        return (lambda: None)
    estado = {"i": 0, "vivo": True}

    def _animar():
        if not estado["vivo"]:
            return
        try:
            if not lbl.winfo_exists():
                return
            lbl.configure(text=f"⏳ {texto}" + "." * (estado["i"] % 4))
            estado["i"] += 1
            lbl.after(400, _animar)
        except Exception:
            pass

    try:
        parent.update_idletasks()
        _animar()
    except Exception:
        pass

    def _detener():
        estado["vivo"] = False
        try:
            if lbl.winfo_exists():
                lbl.destroy()
        except Exception:
            pass
        try:
            parent.update_idletasks()
        except Exception:
            pass

    return _detener


def crear_lista_vacia(parent, texto, subtexto=""):
    """Estado vacío estándar."""
    ctk.CTkLabel(parent, text=texto, text_color="gray",
                 font=ctk.CTkFont(size=13)).pack(pady=(20, 2))
    if subtexto:
        ctk.CTkLabel(parent, text=subtexto, text_color="#9CA3AF",
                     font=ctk.CTkFont(size=11)).pack(pady=(0, 10))


def agregar_detalle_expandible(card, detalle_fn, texto_abrir="▾ Ver detalle", texto_cerrar="▴ Ocultar"):
    """Agrega a una card un bloque detalle colapsable estilo Configuración.

    detalle_fn(frame): puebla el frame detalle (se llama lazy la primera vez que se abre).
    Retorna (toggle_btn, detalle_frame).
    """
    detalle_frame = ctk.CTkFrame(card, fg_color="#F8F5FA", corner_radius=6)
    # no se empaqueta hasta abrir
    estado = {"abierto": False, "cargado": False}

    def _toggle():
        if estado["abierto"]:
            try:
                detalle_frame.pack_forget()
            except Exception:
                pass
            toggle_btn.configure(text=texto_abrir)
            estado["abierto"] = False
        else:
            if not estado["cargado"]:
                try:
                    detalle_fn(detalle_frame)
                except Exception as e:
                    ctk.CTkLabel(detalle_frame, text=f"No se pudo cargar detalle: {e}",
                                 text_color="gray", font=ctk.CTkFont(size=11)).pack(anchor="w", padx=10, pady=4)
                estado["cargado"] = True
            try:
                # el detalle va ENCIMA del botón para que quede visible al abrir
                detalle_frame.pack(fill="x", padx=10, pady=(0, 4), before=toggle_btn)
            except Exception:
                detalle_frame.pack(fill="x", padx=10, pady=(0, 8))
            toggle_btn.configure(text=texto_cerrar)
            estado["abierto"] = True
            try:
                card.update_idletasks()
            except Exception:
                pass

    toggle_btn = ctk.CTkButton(card, text=texto_abrir, width=110, height=26,
                               fg_color="#E5E7EB", text_color="#1F0A33",
                               hover_color="#DDD6E5", command=_toggle)
    return toggle_btn, detalle_frame, _toggle


def linea_detalle(parent, etiqueta, valor):
    """Fila etiqueta: valor estilo Configuración."""
    row = ctk.CTkFrame(parent, fg_color="transparent")
    row.pack(fill="x", padx=10, pady=1)
    ctk.CTkLabel(row, text=f"{etiqueta}:", font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=TITULO_COLOR).pack(side="left")
    ctk.CTkLabel(row, text=str(valor) if valor not in (None, "") else "—",
                 font=ctk.CTkFont(size=11), text_color=DESC_COLOR,
                 justify="left", wraplength=500).pack(side="left", padx=8)
    return row


def crear_tabla_cards(parent, columnas, filas, cap=50, nota_mas=""):
    """Tabla con filas como tarjetas blancas (estilo listas unificadas).

    columnas: [(titulo, ancho)]; filas: [[celda, ...]] donde celda es
    str o (str, {"text_color":..., "weight":...}).
    """
    header = ctk.CTkFrame(parent, fg_color="#DDD6E5", corner_radius=6)
    header.pack(fill="x", padx=5, pady=2)
    for col, (texto, ancho) in enumerate(columnas):
        ctk.CTkLabel(header, text=texto, width=ancho,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=TITULO_COLOR).grid(row=0, column=col, padx=5, pady=5)
    mostrar = filas[:cap] if cap else list(filas)
    for fila in mostrar:
        row = crear_card_interactiva(parent)
        row.pack(fill="x", padx=5, pady=2)
        for col, celda in enumerate(fila):
            if isinstance(celda, tuple):
                texto, opts = celda
            else:
                texto, opts = celda, {}
            ancho = columnas[col][1] if col < len(columnas) else 100
            ctk.CTkLabel(row, text=str(texto), width=ancho,
                         font=ctk.CTkFont(size=11, weight=opts.get("weight", "normal")),
                         text_color=opts.get("text_color", "#1F0A33")).grid(row=0, column=col, padx=5, pady=6)
    if cap and len(filas) > cap:
        ctk.CTkLabel(parent, text=nota_mas or f"Mostrando {cap} de {len(filas)}",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=5)


def crear_tabla_densa(parent, columnas, filas, detalles=None, cap=50, nota_mas=""):
    """Fase 7a: tabla densa modo Excel (header oscuro + filas blancas + ▾ detalle).

    columnas: [(titulo, ancho)]; filas: [[celda, ...]] (celda str o tuple);
    detalles: lista paralela de callables(frame) o None (mismo largo que filas).
    """
    ncols = len(columnas)
    con_detalle = bool(detalles and any(d is not None for d in detalles))
    header = ctk.CTkFrame(parent, fg_color="#3D1559", corner_radius=6)
    header.pack(fill="x", padx=6, pady=(4, 2))
    for col, (texto, ancho) in enumerate(columnas):
        ctk.CTkLabel(header, text=texto, width=ancho,
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="white").grid(row=0, column=col, padx=2, pady=6, sticky="w")
    if con_detalle:
        ctk.CTkLabel(header, text="", width=40).grid(
            row=0, column=ncols, padx=2, pady=6, sticky="w")
    mostrar = filas[:cap] if cap else list(filas)
    dets = list(detalles or [])
    for idx, fila in enumerate(mostrar):
        cont = ctk.CTkFrame(parent, fg_color="white", corner_radius=6)
        cont.pack(fill="x", padx=6, pady=1)
        for col, celda in enumerate(fila):
            if isinstance(celda, tuple):
                texto, opts = celda
            else:
                texto, opts = celda, {}
            ancho = columnas[col][1] if col < ncols else 100
            ctk.CTkLabel(cont, text=str(texto), width=ancho,
                         font=ctk.CTkFont(size=11, weight=opts.get("weight", "normal")),
                         text_color=opts.get("text_color", "#1F0A33")).grid(
                row=0, column=col, padx=2, pady=4, sticky="w")
        poblar = dets[idx] if idx < len(dets) else None
        if poblar is not None:
            detalle = ctk.CTkFrame(cont, fg_color="transparent")
            detalle.grid(row=1, column=0, columnspan=ncols + 1, sticky="ew", padx=10)
            try:
                poblar(detalle)
            except Exception:
                pass
            detalle.grid_remove()
            btn = ctk.CTkButton(cont, text="▾", width=40, height=24,
                                fg_color="transparent", text_color="#7C3AED")
            btn.grid(row=0, column=ncols, padx=2, pady=4)
            btn.configure(command=lambda d=detalle, b=btn: (
                (d.grid_remove(), b.configure(text="▾")) if d.winfo_viewable()
                else (d.grid(), b.configure(text="▴"))))
    if cap and len(filas) > cap:
        ctk.CTkLabel(parent, text=nota_mas or f"Mostrando {cap} de {len(filas)}",
                     text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=5)


def crear_bloque_grafico_tabla(parent, modo_inicial="Ambos"):
    """Segmentado Tabla/Gráfico/Ambos + 2 contenedores. Retorna (frame_grafico, frame_tabla).

    El llamador puebla ambos frames; el toggle muestra/oculta sin re-consultar.
    """
    frame_g = ctk.CTkFrame(parent, fg_color="transparent")
    frame_t = ctk.CTkFrame(parent, fg_color="transparent")

    def _mostrar(modo):
        for f in (frame_g, frame_t):
            try:
                f.pack_forget()
            except Exception:
                pass
        if modo in ("Gráfico", "Ambos"):
            frame_g.pack(fill="x", padx=5, pady=2)
        if modo in ("Tabla", "Ambos"):
            frame_t.pack(fill="x", padx=5, pady=2)

    seg = ctk.CTkSegmentedButton(parent, values=["Tabla", "Gráfico", "Ambos"], command=_mostrar)
    try:
        seg.set(modo_inicial)
    except Exception:
        pass
    seg.pack(anchor="e", padx=8, pady=4)
    _mostrar(modo_inicial)
    return frame_g, frame_t
