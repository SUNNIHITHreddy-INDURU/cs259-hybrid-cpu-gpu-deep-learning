%% =====================================================================
%%  cs259.cls  --  CS 259 (Advanced Parallel Processing) term-paper class
%%
%%  Replicates the instructor's ACM-style Word template:
%%    * US Letter; text block 7 in x 9.25 in, 1 in from top and bottom,
%%      0.75 in left/right margins; two 3.33 in columns, 0.33 in gutter
%%    * Times 9 pt justified body text, Helvetica title block
%%    * numbered ALL-CAPS section heads, subsection / subsubsection heads
%%    * captions: Times 9 pt bold, "Figure 1." below figures,
%%      "Table 1." above tables
%%    * numbered reference list, 9 pt, ragged right, hanging indent
%%    * no headers, footers or page numbers
%%    * balanced columns on the last page
%%
%%  Works with pdfLaTeX (Overleaf default) and with XeLaTeX/LuaLaTeX
%%  (and tectonic).  Class options:
%%     siunitx   load siunitx
%%     indent    indent paragraphs instead of the template's 6 pt gap
%%     nobalance do not balance the columns of the last page
%% =====================================================================
\NeedsTeXFormat{LaTeX2e}[2005/12/01]
\ProvidesClass{cs259}[2026/11/15 v1.0 CS 259 term paper class]

%% ---------------------------------------------------------------- options
\newif\ifcs@siunitx
\newif\ifcs@indent
\newif\ifcs@balance \cs@balancetrue
\DeclareOption{siunitx}{\cs@siunitxtrue}
\DeclareOption{indent}{\cs@indenttrue}
\DeclareOption{nobalance}{\cs@balancefalse}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions\relax
\LoadClass[10pt,letterpaper,twocolumn]{article}

%% ------------------------------------------------------- engine detection
\newif\ifcs@unicode
\ifdefined\XeTeXversion \cs@unicodetrue \fi
\ifdefined\directlua    \cs@unicodetrue \fi

%% ------------------------------------------------------------------ fonts
%% Text: Times-compatible serif; Helvetica-compatible sans for the title
%% block; a small monospaced face for code.
\ifcs@unicode
  %% XeLaTeX / LuaLaTeX / tectonic: TeX Gyre Termes (Times), Heros (Helvetica)
  \RequirePackage{fontspec}
  \setmainfont{texgyretermes}[Extension=.otf,%
    UprightFont=*-regular,BoldFont=*-bold,%
    ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
  \setsansfont{texgyreheros}[Extension=.otf,%
    UprightFont=*-regular,BoldFont=*-bold,%
    ItalicFont=*-italic,BoldItalicFont=*-bolditalic]
  \setmonofont{lmmono10-regular}[Extension=.otf,%
    UprightFont=*,BoldFont=*,ItalicFont=lmmono10-italic,BoldItalicFont=lmmono10-italic]
  \RequirePackage{amsmath}
  \RequirePackage{unicode-math}
  \setmathfont{texgyretermes-math.otf}
\else
  %% pdfLaTeX: Nimbus/Times via psnfss (always part of TeX Live)
  \RequirePackage[T1]{fontenc}
  \RequirePackage[utf8]{inputenc}
  \RequirePackage{textcomp}
  \RequirePackage{mathptmx}                 % Times text and math
  \RequirePackage[scaled=1]{helvet}         % Helvetica, exact size
  \renewcommand{\ttdefault}{lmtt}           % Latin Modern Typewriter
  \RequirePackage{amsmath}
  \RequirePackage{amssymb}
\fi

%% -------------------------------------------------------------- page size
\setlength{\paperwidth}{8.5in}
\setlength{\paperheight}{11in}
\ifdefined\XeTeXversion
  \AtBeginDocument{\special{papersize=\the\paperwidth,\the\paperheight}}
\else
  \ifdefined\pdfpagewidth
    \pdfpagewidth=\paperwidth \pdfpageheight=\paperheight
  \else
    \ifdefined\pagewidth
      \pagewidth=\paperwidth \pageheight=\paperheight
    \fi
  \fi
\fi

%% ---------------------------------------------------------- page geometry
%% Text block: 7 in x 9.25 in; left edge 0.75 in; top edge 1 in.
%% All layout lengths use bp (1/72 in), the unit of the template (Word "points"),
%% not TeX points (1/72.27 in).
\setlength{\textwidth}{504bp}          % 7 in
\setlength{\textheight}{664bp}         % 9.25 in minus 2 bp so that descenders of the last line stay inside the rectangle
\setlength{\columnsep}{24bp}           % gutter; columns are (504-24)/2 = 240 bp = 3.33 in
\setlength{\columnseprule}{0pt}
\setlength{\hoffset}{0pt}
\setlength{\voffset}{0pt}
\setlength{\oddsidemargin}{-18bp}      % 54 bp (0.75 in) minus TeX's 1 in origin
\setlength{\evensidemargin}{-18bp}
\setlength{\topmargin}{0pt}            % text starts 72 bp = 1 in from the top
\setlength{\headheight}{0pt}
\setlength{\headsep}{0pt}
\setlength{\footskip}{0pt}
\setlength{\marginparwidth}{0pt}
\setlength{\marginparsep}{0pt}
\setlength{\marginparpush}{0pt}
\setlength{\topskip}{8.1bp}            % body text: first baseline 8.1 bp below the top margin
\setlength{\maxdepth}{.5\topskip}

%% -------------------------------------------- no headers/footers/numbers
\pagestyle{empty}
\let\ps@plain\ps@empty
\let\ps@headings\ps@empty
\let\ps@myheadings\ps@empty

%% ------------------------------------------------------------ font sizes
%% Sizes and leading are given in bp so that "9 pt" means the same 9/72 in as
%% in the Word template.  \cs@setsize\cmd{size}{leading} (bp);
%% \cs@fontsize{size}{leading} selects a size; \cs@mathsizes sets script sizes.
\newcommand\cs@setsize[3]{%
  \edef\cs@x{\noexpand\@setfontsize\noexpand#1{\strip@pt\dimexpr#2bp\relax}%
    {\strip@pt\dimexpr#3bp\relax}}\cs@x}
\newcommand\cs@fontsize[2]{%
  \edef\cs@x{\noexpand\fontsize{\strip@pt\dimexpr#1bp\relax}%
    {\strip@pt\dimexpr#2bp\relax}}\cs@x\selectfont}
\newcommand\cs@mathsizes[3]{%
  \edef\cs@x{\noexpand\DeclareMathSizes{\strip@pt\dimexpr#1bp\relax}%
    {\strip@pt\dimexpr#1bp\relax}{\strip@pt\dimexpr#2bp\relax}%
    {\strip@pt\dimexpr#3bp\relax}}\cs@x}

%% Body: Times 9 on 10.35 (single spacing of a 9 pt Times line in Word).
\renewcommand\normalsize{%
  \cs@setsize\normalsize{9}{10.35}%
  \abovedisplayskip 6bp \@plus1\p@ \@minus2\p@
  \abovedisplayshortskip \z@ \@plus2\p@
  \belowdisplayshortskip 3bp \@plus1\p@ \@minus1\p@
  \belowdisplayskip \abovedisplayskip
  \let\@listi\@listI}
\renewcommand\small{%
  \cs@setsize\small{8}{9.2}%
  \abovedisplayskip 5bp \@plus1\p@ \@minus2\p@
  \abovedisplayshortskip \z@ \@plus1\p@
  \belowdisplayshortskip 2.5bp \@plus1\p@ \@minus1\p@
  \belowdisplayskip \abovedisplayskip
  \def\@listi{\leftmargin\leftmargini \topsep \z@ \@plus1\p@ \@minus1\p@
    \parsep \z@ \@plus.5\p@ \itemsep 1bp \@plus.5\p@}}
%% The template prescribes 9 pt footnotes.
\renewcommand\footnotesize{\cs@setsize\footnotesize{9}{10.35}%
  \let\@listi\@listI}
\renewcommand\scriptsize{\cs@setsize\scriptsize{7}{8}}
\renewcommand\tiny{\cs@setsize\tiny{5.5}{6.5}}
\renewcommand\large{\cs@setsize\large{11}{12.65}}
\renewcommand\Large{\cs@setsize\Large{12}{13.8}}
\renewcommand\LARGE{\cs@setsize\LARGE{14}{16.1}}
\renewcommand\huge{\cs@setsize\huge{18}{20.7}}
\renewcommand\Huge{\cs@setsize\Huge{18}{20.7}}
\cs@mathsizes{9}{6.5}{5}
\cs@mathsizes{8}{6}{5}
\cs@mathsizes{7}{5}{5}
\cs@mathsizes{11}{8}{6}
\cs@mathsizes{12}{8.5}{6}
\cs@mathsizes{14}{10}{7}
\cs@mathsizes{18}{12}{9}

\def\@listI{\leftmargin\leftmargini
  \topsep \z@ \@plus1\p@ \@minus1\p@     % \parskip is added by LaTeX
  \parsep \z@ \@plus.5\p@
  \itemsep 1.5bp \@plus.5\p@}
\let\@listi\@listI
\setlength\leftmargini{14bp}
\setlength\leftmarginii{12bp}
\setlength\leftmarginiii{10bp}
\setlength\leftmarginiv{10bp}
\setlength\labelsep{4bp}
\setlength\labelwidth{\leftmargini}\addtolength\labelwidth{-\labelsep}
\normalsize

%% ------------------------------------------------- paragraphs, justification
%% The template separates paragraphs by a 6 pt gap without indentation.
\ifcs@indent
  \setlength{\parindent}{9bp}
  \setlength{\parskip}{\z@ \@plus .3\p@}
\else
  \setlength{\parindent}{\z@}
  \setlength{\parskip}{6bp \@plus 1.5\p@ \@minus .5\p@}
\fi
\tolerance=1000
\emergencystretch=1.5em
\hbadness=2000
\hfuzz=0.5pt
\vbadness=10000
\clubpenalty=5000
\widowpenalty=5000
\flushbottom

%% ------------------------------------------------------------- packages
\RequirePackage{graphicx}
\RequirePackage{xcolor}
\RequirePackage{booktabs}
\RequirePackage{array}
\ifcs@siunitx \RequirePackage{siunitx}\fi
%% microtype is optional: it only improves line breaking.
\IfFileExists{microtype.sty}{%
  \ifcs@unicode
    \RequirePackage{microtype}%
  \else
    \RequirePackage[protrusion=true,expansion=true,final]{microtype}%
  \fi}{}
\PassOptionsToPackage{hyphens}{url}
\RequirePackage{listings}
%% sorts and compresses citation lists: [3, 4] and [3--5]
\IfFileExists{cite.sty}{\RequirePackage{cite}}{}

%% ------------------------------------------------------ section headings
\setcounter{secnumdepth}{4}
\newlength{\cs@labelwd}
\setlength{\cs@labelwd}{36bp}      % heading text starts 0.5 in right of the number
\def\cs@punct@section{.}
\def\cs@punct@subsection{}
\def\cs@punct@subsubsection{}
\def\cs@punct@paragraph{}
%% The zero-width strut makes a heading at the very top of a column sit lower
%% than body text there (as in the template); it has no effect elsewhere.
\def\cs@strut@section{11bp}
\def\cs@strut@subsection{11bp}
\def\cs@strut@subsubsection{10bp}
\def\cs@strut@paragraph{10bp}
\renewcommand\@seccntformat[1]{%
  \hb@xt@\cs@labelwd{\vrule\@height\csname cs@strut@#1\endcsname\@width\z@\@depth\z@
    \csname the#1\endcsname\csname cs@punct@#1\endcsname\hfil}}

%% LaTeX adds \parskip before the first paragraph below a heading; the
%% template does not, so cancel it once the heading has been set.
\def\@afterheading{%
  \@nobreaktrue
  \nobreak\vskip-\parskip
  \everypar{%
    \if@nobreak
      \@nobreakfalse
      \clubpenalty\@M
      \if@afterindent \else {\setbox\z@\lastbox}\fi
    \else
      \clubpenalty\@clubpenalty
      \everypar{}%
    \fi}}
%% Same correction when a list directly follows a heading.
\let\cs@orig@trivlist\@trivlist
\def\@trivlist{\ifvmode\if@nobreak\nobreak\vskip\parskip\fi\fi\cs@orig@trivlist}

\newcommand\cs@sectionfont{\normalfont\cs@fontsize{12}{13.8}\bfseries
  \raggedright \hyphenpenalty\@M \exhyphenpenalty\@M \vskip-.6bp}
\newcommand\cs@subsubsectionfont{\normalfont\cs@fontsize{11}{12.65}\itshape
  \raggedright \hyphenpenalty\@M \exhyphenpenalty\@M \vskip-.6bp}

\renewcommand\section{\@startsection{section}{1}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.75bp}{\cs@sectionfont\MakeUppercase}}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.75bp}{\cs@sectionfont}}
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.75bp}{\cs@subsubsectionfont}}
\renewcommand\paragraph{\@startsection{paragraph}{4}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.75bp}{\cs@subsubsectionfont}}
\renewcommand\subparagraph{\@startsection{subparagraph}{5}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.75bp}{\cs@subsubsectionfont}}

%% ----------------------------------------------------------- title block
%%   \title{...}  (use \\ for a line break)   \author{...}
%%   \affiliation{line 1\\line 2\\...}        \email{...}
\newcommand{\affiliation}[1]{\gdef\cs@affiliation{#1}}
\newcommand{\email}[1]{\gdef\cs@email{#1}}
\gdef\cs@affiliation{}
\gdef\cs@email{}

\newcommand\cs@titlefont{\sffamily\bfseries\cs@fontsize{18}{22.7}}
\newcommand\cs@authorfont{\sffamily\mdseries\cs@fontsize{12}{19.92}}
\newcommand\cs@affilfont{\sffamily\mdseries\cs@fontsize{10}{12.6}}
\newcommand\cs@emailfont{\sffamily\mdseries\cs@fontsize{12}{18.5}}

\newcommand\cs@maketitle{%
  \vbox{%
    \hsize\textwidth \linewidth\hsize \parindent\z@ \parskip\z@skip
    \centering
    \let\footnote\@gobble
    {\cs@titlefont \leavevmode\rule{\z@}{17.3bp}\@title\par}%
    {\cs@authorfont \@author\par}%
    \vskip .6bp
    \ifx\cs@affiliation\@empty\else{\cs@affilfont \cs@affiliation\par}\fi
    \ifx\cs@email\@empty\else{\cs@emailfont \cs@email\par}\fi
    \vskip \cs@titlegap
  }}
\newlength{\cs@titlegap}
\setlength{\cs@titlegap}{25.1bp}

\renewcommand\maketitle{%
  \par
  \twocolumn[\cs@maketitle]%
  \thispagestyle{empty}%
  \global\let\maketitle\relax
  \global\let\cs@maketitle\relax
  \global\let\@maketitle\relax
  \global\let\title\relax
  \global\let\author\relax}

%% Abstract: unnumbered head (same style as section heads), 9 pt text.
\renewenvironment{abstract}{\section*{\vrule\@height11bp\@width\z@\@depth\z@ Abstract}}{\par}

%% ------------------------------------------------------ floats & captions
\setcounter{topnumber}{3}
\setcounter{bottomnumber}{2}
\setcounter{totalnumber}{5}
\setcounter{dbltopnumber}{2}
\renewcommand\topfraction{.9}
\renewcommand\bottomfraction{.5}
\renewcommand\textfraction{.1}
\renewcommand\floatpagefraction{.7}
\renewcommand\dbltopfraction{.9}
\renewcommand\dblfloatpagefraction{.7}
\setlength\floatsep{9bp \@plus 2\p@ \@minus 2\p@}
\setlength\textfloatsep{12bp \@plus 2\p@ \@minus 4\p@}
\setlength\intextsep{9bp \@plus 2\p@ \@minus 2\p@}
\setlength\dblfloatsep{9bp \@plus 2\p@ \@minus 2\p@}
\setlength\dbltextfloatsep{12bp \@plus 2\p@ \@minus 4\p@}
\setlength\@fptop{0\p@ \@plus 1fil}
\setlength\@fpsep{8\p@ \@plus 2fil}
\setlength\@fpbot{0\p@ \@plus 1fil}
\setlength\@dblfptop{0\p@ \@plus 1fil}
\setlength\@dblfpsep{8\p@ \@plus 2fil}
\setlength\@dblfpbot{0\p@ \@plus 1fil}
\setlength\abovecaptionskip{6bp}
\setlength\belowcaptionskip{6bp}

\newcommand\cs@capfont{\normalfont\normalsize\bfseries}
%% "Table" text size; override with \renewcommand{\tablefont}{...}
\newcommand\tablefont{\small}
\def\cs@tabletype{table}
%% Figure captions (any non-table float): centred BELOW the figure.
%% Table captions: centred ABOVE the table.
\long\def\@makecaption#1#2{%
  \ifx\@captype\cs@tabletype\else \vskip\abovecaptionskip \fi
  \sbox\@tempboxa{\cs@capfont #1. #2}%
  \ifdim \wd\@tempboxa >\hsize
    {\cs@capfont \centering \parindent\z@ \parskip\z@skip #1. #2\par}%
  \else
    \global\@minipagefalse
    \hb@xt@\hsize{\hfil\box\@tempboxa\hfil}%
  \fi
  \ifx\@captype\cs@tabletype \vskip\belowcaptionskip \fi}

\def\@floatboxreset{%
  \reset@font \normalsize \@setminipage
  \centering \parskip\z@skip \parindent\z@
  \ifx\@captype\cs@tabletype \tablefont \fi}

\renewcommand\fnum@figure{\figurename~\thefigure}
\renewcommand\fnum@table{\tablename~\thetable}

%% Tables: compact spacing; booktabs rules.
\setlength\tabcolsep{4bp}
\renewcommand\arraystretch{1.08}
\setlength\heavyrulewidth{.8\p@}
\setlength\lightrulewidth{.4\p@}
\setlength\aboverulesep{.4ex}
\setlength\belowrulesep{.5ex}

%% ---- helpers for figures and tables ----------------------------------
%%  \colfigure[pos][width]{file}{caption}{label}    one column (default tb)
%%  \widefigure[pos][width]{file}{caption}{label}   spans both columns (t)
%%  \begin{coltable}[pos]{caption}{label} ... \end{coltable}
%%  \begin{widetable}[pos]{caption}{label} ... \end{widetable}
%%  \fitcol{<tabular>}  \fitwide{<tabular>}   scale a tabular to the width
\NewDocumentCommand\colfigure{O{tb} O{\columnwidth} m m m}{%
  \begin{figure}[#1]\centering
    \includegraphics[width=#2]{#3}%
    \caption{#4}\label{#5}%
  \end{figure}}
\NewDocumentCommand\widefigure{O{t} O{\textwidth} m m m}{%
  \begin{figure*}[#1]\centering
    \includegraphics[width=#2]{#3}%
    \caption{#4}\label{#5}%
  \end{figure*}}
\NewDocumentEnvironment{coltable}{O{tb} m m}%
  {\begin{table}[#1]\caption{#2}\label{#3}}%
  {\end{table}}
\NewDocumentEnvironment{widetable}{O{t} m m}%
  {\begin{table*}[#1]\caption{#2}\label{#3}}%
  {\end{table*}}
\newcommand\fitcol[1]{\resizebox{\columnwidth}{!}{#1}}
\newcommand\fitwide[1]{\resizebox{\textwidth}{!}{#1}}

%% ------------------------------------------------------ cross-reference
\newcommand\secref[1]{Section~\ref{#1}}
\newcommand\figref[1]{Figure~\ref{#1}}
\newcommand\tabref[1]{Table~\ref{#1}}
\newcommand\eqnref[1]{Eq.~(\ref{#1})}

%% -------------------------------------------------------- inline code
%% \code{omp_set_num_threads}: monospaced 8 pt.  Underscores, #, ^, ~, &, $,
%% < > " | need no escaping; \_ \# \% \& \$ \{ \} are also accepted.
%% (Not usable inside the argument of \verb or \lstinline.)
\ExplSyntaxOn
\bool_new:N \l__cs_code_bs_bool      % previous char was a backslash
\bool_new:N \l__cs_code_hash_bool    % previous char was the first of a ## pair
\int_new:N  \l__cs_code_p_int        % code of previous printed char
\int_new:N  \l__cs_code_pp_int       % code of the char before that
%% print one character.  Preferred break points (penalty 0): after "/" ","
%% and after a single "_"; elsewhere a discouraged break (penalty 3000) is
%% allowed so that a long token can never overflow the narrow column.
\cs_new_protected:Npn \__cs_code_out:N #1 {
  \int_compare:nNnF { \l__cs_code_p_int } = { 0 }
    {
      \bool_if:nTF
        {
          \int_compare_p:nNn { `#1 } > { 0 } &&
          ( \int_compare_p:nNn \l__cs_code_p_int = { 47 } ||
            \int_compare_p:nNn \l__cs_code_p_int = { 44 } ||
            ( \int_compare_p:nNn \l__cs_code_p_int = { 95 } &&
              !\int_compare_p:nNn \l__cs_code_pp_int = { 95 } &&
              !\int_compare_p:nNn { `#1 } = { 95 } ) )
        }
        { \penalty\c_zero_int \scan_stop: }
        { \penalty 3000 \scan_stop: }
    }
  #1
  \int_set_eq:NN \l__cs_code_pp_int \l__cs_code_p_int
  \int_set:Nn \l__cs_code_p_int { `#1 }
}
\cs_new_protected:Npn \__cs_code_char:N #1 {
  \str_if_eq:nnTF {#1} { ~ }
    {
      \bool_if:NT \l__cs_code_bs_bool { \__cs_code_out:N \c_backslash_str }
      \bool_set_false:N \l__cs_code_bs_bool
      \ 
      \int_set_eq:NN \l__cs_code_pp_int \l__cs_code_p_int
      \int_set:Nn \l__cs_code_p_int { 32 }
    }
    {
      \bool_if:NTF \l__cs_code_bs_bool
        {
          \bool_set_false:N \l__cs_code_bs_bool
          \int_case:nnF { `#1 }
            { { 95 } { } { 35 } { } { 37 } { } { 38 } { } { 36 } { } { 123 } { } { 125 } { } }
            { \__cs_code_out:N \c_backslash_str }
          \__cs_code_out:N #1
        }
        {
          \int_compare:nNnTF { `#1 } = { 92 }
            { \bool_set_true:N \l__cs_code_bs_bool }
            {
              \int_compare:nNnTF { `#1 } = { 35 }
                {
                  \bool_if:NTF \l__cs_code_hash_bool
                    { \bool_set_false:N \l__cs_code_hash_bool }
                    { \bool_set_true:N \l__cs_code_hash_bool \__cs_code_out:N #1 }
                }
                { \__cs_code_out:N #1 }
            }
        }
    }
}
\DeclareRobustCommand \code [1] {
  \group_begin:
    \bool_set_false:N \l__cs_code_bs_bool
    \bool_set_false:N \l__cs_code_hash_bool
    \int_zero:N \l__cs_code_p_int
    \int_zero:N \l__cs_code_pp_int
    \ttfamily \mdseries \fontsize{8.03}{10.3888}\selectfont
    \str_map_function:nN {#1} \__cs_code_char:N
    \bool_if:NT \l__cs_code_bs_bool { \c_backslash_str }
  \group_end:
}
\ExplSyntaxOff

%% ------------------------------------------------------------ listings
\definecolor{cs@kw}{rgb}{0.10,0.20,0.55}
\definecolor{cs@cm}{gray}{0.40}
\definecolor{cs@st}{rgb}{0.45,0.12,0.12}
\lstdefinestyle{cs259}{%
  basicstyle=\ttfamily\mdseries\cs@fontsize{7.5}{8.7},
  keywordstyle=\color{cs@kw},
  commentstyle=\itshape\color{cs@cm},
  stringstyle=\color{cs@st},
  identifierstyle=\color{black},
  showstringspaces=false,
  keepspaces=true,
  columns=fullflexible,
  tabsize=2,
  breaklines=true,
  breakatwhitespace=false,
  postbreak=\mbox{\textcolor{cs@cm}{\tiny\ensuremath{\rightarrow}}\space},
  frame=tb,
  framerule=.4pt,
  rulecolor=\color{cs@cm},
  framesep=2pt,
  xleftmargin=0pt,
  xrightmargin=0pt,
  aboveskip=3pt,
  belowskip=3pt,
  numbers=none,
  captionpos=b,
  upquote=true}
\lstdefinelanguage{CUDA}[]{C++}{%
  morekeywords={__global__,__device__,__host__,__shared__,__constant__,%
    __restrict__,__syncthreads,__launch_bounds__,__forceinline__,%
    threadIdx,blockIdx,blockDim,gridDim,warpSize,dim3,%
    cudaMalloc,cudaMallocHost,cudaFree,cudaFreeHost,cudaMemcpy,%
    cudaMemcpyAsync,cudaMemset,cudaMemcpyHostToDevice,%
    cudaMemcpyDeviceToHost,cudaDeviceSynchronize,cudaGetLastError,%
    cudaStream_t,cudaStreamCreate,cudaStreamDestroy,cudaStreamSynchronize,%
    cudaEvent_t,cudaEventCreate,cudaEventRecord,cudaEventSynchronize,%
    cudaEventElapsedTime,cudaSetDevice,cudaError_t}}
\lstset{style=cs259,language=C++}
\renewcommand\lstlistingname{Listing}

%% -------------------------------------------------- references list
%% Numbered [1], [2], ... (BibTeX style cs259.bst sorts by first author; the paper uses cs259ieee.bst, see main.tex),
%% 9 pt, ragged right, hanging indent; the heading is a numbered section.
\newcommand\cs@raggedright{%
  \rightskip=0pt \@plus 3em \relax \leftskip=\z@skip
  \spaceskip=.333em \@plus .15em \@minus .08em \relax
  \xspaceskip=.5em \relax
  \parfillskip=\z@ \@plus 1fil}
\newcommand\csReferencesIntro{}% text under the References heading; redefine in main.tex
\renewenvironment{thebibliography}[1]{%
  \section{References}%
  \csReferencesIntro
  \list{\@biblabel{\@arabic\c@enumiv}}%
    {\settowidth\labelwidth{\@biblabel{99}}%
     \setlength\leftmargin{18bp}%
     \setlength\labelsep{2bp}%
     \setlength\labelwidth{16bp}%
     \setlength\itemindent{\z@}%
     \setlength\topsep{\z@}%
     \setlength\partopsep{\z@}%
     \setlength\parsep{\z@}%
     \setlength\itemsep{4bp \@plus 2\p@ \@minus 1\p@}%
     \usecounter{enumiv}%
     \let\p@enumiv\@empty
     \renewcommand\theenumiv{\@arabic\c@enumiv}}%
  \normalsize\cs@raggedright
  \clubpenalty4000 \@clubpenalty\clubpenalty \widowpenalty4000
  \sfcode`\.\@m}
 {\def\@noitemerr{\@latex@warning{Empty `thebibliography' environment}}%
  \endlist}
\renewcommand\@biblabel[1]{[#1]\hfil}

%% --------------------------------------------- hyperlinks, URLs, metadata
\RequirePackage[hidelinks,bookmarks=false,pdfborder={0 0 0},%
  breaklinks=true,unicode=true]{hyperref}
\urlstyle{same}
%% URLs may break after / . ? = & - ; a break after ":" (as in "https:") is
%% strongly discouraged by a high penalty.
\AtBeginDocument{\Urlmuskip=0mu plus 1mu\relax
  \mathchardef\UrlBigBreakPenalty=5000\relax}

%% ---------------------------------------- balance the last page's columns
\ifcs@balance
  \IfFileExists{flushend.sty}{\RequirePackage{flushend}}{%
    \ClassWarning{cs259}{flushend.sty not found; last-page columns will not be balanced}}
\fi

\endinput
