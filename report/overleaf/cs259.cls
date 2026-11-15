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
\setlength{\textwidth}{504pt}          % 7 in
\setlength{\textheight}{666pt}         % 9.25 in
\setlength{\columnsep}{24pt}           % 0.33 in gutter -> 240 pt (3.33 in) columns
\setlength{\columnseprule}{0pt}
\setlength{\hoffset}{0pt}
\setlength{\voffset}{0pt}
\setlength{\oddsidemargin}{-18pt}      % 54 pt - 1 in
\setlength{\evensidemargin}{-18pt}
\setlength{\topmargin}{0pt}            % 72 pt from the top
\setlength{\headheight}{0pt}
\setlength{\headsep}{0pt}
\setlength{\footskip}{0pt}
\setlength{\marginparwidth}{0pt}
\setlength{\marginparsep}{0pt}
\setlength{\marginparpush}{0pt}
\setlength{\topskip}{10.5pt}
\setlength{\maxdepth}{.5\topskip}

%% -------------------------------------------- no headers/footers/numbers
\pagestyle{empty}
\let\ps@plain\ps@empty
\let\ps@headings\ps@empty
\let\ps@myheadings\ps@empty

%% ------------------------------------------------------------ font sizes
%% Body: Times 9 pt on 10.35 pt (single spacing of a 9 pt Times line).
\renewcommand\normalsize{%
  \@setfontsize\normalsize{9}{10.35}%
  \abovedisplayskip 6\p@ \@plus1\p@ \@minus2\p@
  \abovedisplayshortskip \z@ \@plus2\p@
  \belowdisplayshortskip 3\p@ \@plus1\p@ \@minus1\p@
  \belowdisplayskip \abovedisplayskip
  \let\@listi\@listI}
\renewcommand\small{%
  \@setfontsize\small{8}{9.2}%
  \abovedisplayskip 5\p@ \@plus1\p@ \@minus2\p@
  \abovedisplayshortskip \z@ \@plus1\p@
  \belowdisplayshortskip 2.5\p@ \@plus1\p@ \@minus1\p@
  \belowdisplayskip \abovedisplayskip
  \def\@listi{\leftmargin\leftmargini \topsep 3\p@ \@plus1\p@ \@minus1\p@
    \parsep \z@ \@plus.5\p@ \itemsep 1\p@ \@plus.5\p@}}
%% The template prescribes 9 pt footnotes.
\renewcommand\footnotesize{\@setfontsize\footnotesize{9}{10.35}%
  \let\@listi\@listI}
\renewcommand\scriptsize{\@setfontsize\scriptsize{7}{8}}
\renewcommand\tiny{\@setfontsize\tiny{5.5}{6.5}}
\renewcommand\large{\@setfontsize\large{11}{12.65}}
\renewcommand\Large{\@setfontsize\Large{12}{13.8}}
\renewcommand\LARGE{\@setfontsize\LARGE{14}{16.1}}
\renewcommand\huge{\@setfontsize\huge{18}{20.7}}
\renewcommand\Huge{\@setfontsize\Huge{18}{20.7}}
\DeclareMathSizes{9}{9}{6.5}{5}
\DeclareMathSizes{8}{8}{6}{5}
\DeclareMathSizes{7}{7}{5}{5}
\DeclareMathSizes{11}{11}{8}{6}
\DeclareMathSizes{12}{12}{8.5}{6}
\DeclareMathSizes{14}{14}{10}{7}
\DeclareMathSizes{18}{18}{12}{9}

\def\@listI{\leftmargin\leftmargini
  \topsep 3\p@ \@plus1\p@ \@minus1\p@
  \parsep \z@ \@plus.5\p@
  \itemsep 1.5\p@ \@plus.5\p@}
\let\@listi\@listI
\setlength\leftmargini{14\p@}
\setlength\leftmarginii{12\p@}
\setlength\leftmarginiii{10\p@}
\setlength\leftmarginiv{10\p@}
\setlength\labelsep{4\p@}
\setlength\labelwidth{\leftmargini}\addtolength\labelwidth{-\labelsep}
\normalsize

%% ------------------------------------------------- paragraphs, justification
%% The template separates paragraphs by a 6 pt gap without indentation.
\ifcs@indent
  \setlength{\parindent}{9\p@}
  \setlength{\parskip}{\z@ \@plus .3\p@}
\else
  \setlength{\parindent}{\z@}
  \setlength{\parskip}{6\p@ \@plus 1.5\p@ \@minus .5\p@}
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

%% ------------------------------------------------------ section headings
\setcounter{secnumdepth}{4}
\newlength{\cs@labelwd}
\setlength{\cs@labelwd}{36pt}      % heading text starts 0.5 in right of the number
\def\cs@punct@section{.}
\def\cs@punct@subsection{}
\def\cs@punct@subsubsection{}
\def\cs@punct@paragraph{}
\renewcommand\@seccntformat[1]{%
  \hb@xt@\cs@labelwd{\csname the#1\endcsname\csname cs@punct@#1\endcsname\hfil}}

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

\newcommand\cs@sectionfont{\normalfont\fontsize{12}{13.8}\selectfont\bfseries}
\newcommand\cs@subsubsectionfont{\normalfont\fontsize{11}{12.65}\selectfont\itshape}

\renewcommand\section{\@startsection{section}{1}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.3\p@}{\cs@sectionfont\MakeUppercase}}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.3\p@}{\cs@sectionfont}}
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.3\p@}{\cs@subsubsectionfont}}
\renewcommand\paragraph{\@startsection{paragraph}{4}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.3\p@}{\cs@subsubsectionfont}}
\renewcommand\subparagraph{\@startsection{subparagraph}{5}{\z@}%
  {\z@ \@plus 1\p@ \@minus 1\p@}{.3\p@}{\cs@subsubsectionfont}}

%% ----------------------------------------------------------- title block
%%   \title{...}  (use \\ for a line break)   \author{...}
%%   \affiliation{line 1\\line 2\\...}        \email{...}
\newcommand{\affiliation}[1]{\gdef\cs@affiliation{#1}}
\newcommand{\email}[1]{\gdef\cs@email{#1}}
\gdef\cs@affiliation{}
\gdef\cs@email{}

\newcommand\cs@titlefont{\sffamily\bfseries\fontsize{18}{22.7}\selectfont}
\newcommand\cs@authorfont{\sffamily\mdseries\fontsize{12}{20}\selectfont}
\newcommand\cs@affilfont{\sffamily\mdseries\fontsize{10}{12.6}\selectfont}
\newcommand\cs@emailfont{\sffamily\mdseries\fontsize{12}{18.5}\selectfont}

\newcommand\cs@maketitle{%
  \vbox{%
    \hsize\textwidth \linewidth\hsize \parindent\z@ \parskip\z@skip
    \centering
    \let\footnote\@gobble
    {\cs@titlefont \leavevmode\rule{\z@}{17.1pt}\@title\par}%
    {\cs@authorfont \@author\par}%
    \vskip .6pt
    \ifx\cs@affiliation\@empty\else{\cs@affilfont \cs@affiliation\par}\fi
    \ifx\cs@email\@empty\else{\cs@emailfont \cs@email\par}\fi
    \vskip \cs@titlegap
  }}
\newlength{\cs@titlegap}
\setlength{\cs@titlegap}{0pt}

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
\renewenvironment{abstract}{\section*{Abstract}}{\par}

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
\setlength\floatsep{9\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\textfloatsep{12\p@ \@plus 2\p@ \@minus 4\p@}
\setlength\intextsep{9\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\dblfloatsep{9\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\dbltextfloatsep{12\p@ \@plus 2\p@ \@minus 4\p@}
\setlength\@fptop{0\p@ \@plus 1fil}
\setlength\@fpsep{8\p@ \@plus 2fil}
\setlength\@fpbot{0\p@ \@plus 1fil}
\setlength\@dblfptop{0\p@ \@plus 1fil}
\setlength\@dblfpsep{8\p@ \@plus 2fil}
\setlength\@dblfpbot{0\p@ \@plus 1fil}
\setlength\abovecaptionskip{6\p@}
\setlength\belowcaptionskip{6\p@}

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
\setlength\tabcolsep{4\p@}
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
%% \code{omp_set_num_threads} or \code{omp\_set\_num\_threads}: both work.
\ExplSyntaxOn
\str_new:N \l__cs_code_str
\DeclareRobustCommand \code [1] {
  \group_begin:
    \str_set:Nn \l__cs_code_str {#1}
    \str_replace_all:Nnn \l__cs_code_str { \_ } { _ }
    \str_replace_all:Nnn \l__cs_code_str { \# } { # }
    \str_replace_all:Nnn \l__cs_code_str { \% } { % }
    \str_replace_all:Nnn \l__cs_code_str { \& } { & }
    \str_replace_all:Nnn \l__cs_code_str { \$ } { $ }
    \str_replace_all:Nnn \l__cs_code_str { \{ } { \c_left_brace_str }
    \str_replace_all:Nnn \l__cs_code_str { \} } { \c_right_brace_str }
    \str_replace_all:Nnn \l__cs_code_str { ## } { # }
    \ttfamily \mdseries \fontsize{8}{10.35} \selectfont
    \l__cs_code_str
  \group_end:
}
\ExplSyntaxOff

%% ------------------------------------------------------------ listings
\definecolor{cs@kw}{rgb}{0.10,0.20,0.55}
\definecolor{cs@cm}{gray}{0.40}
\definecolor{cs@st}{rgb}{0.45,0.12,0.12}
\lstdefinestyle{cs259}{%
  basicstyle=\ttfamily\mdseries\fontsize{7.5}{8.7}\selectfont,
  keywordstyle=\color{cs@kw},
  directivestyle=\color{cs@kw},
  commentstyle=\itshape\color{cs@cm},
  stringstyle=\color{cs@st},
  identifierstyle=\color{black},
  showstringspaces=false,
  keepspaces=true,
  columns=fullflexible,
  tabsize=2,
  breaklines=true,
  breakatwhitespace=false,
  prebreak=\mbox{\textcolor{cs@cm}{\tiny\ensuremath{\hookleftarrow}}},
  postbreak=\mbox{\textcolor{cs@cm}{\tiny\ensuremath{\hookrightarrow}}\space},
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
%% Numbered [1], [2], ... (BibTeX style cs259.bst sorts by first author),
%% 9 pt, ragged right, hanging indent; the heading is a numbered section.
\newcommand\cs@raggedright{%
  \rightskip=0pt \@plus 3em \relax \leftskip=\z@skip
  \spaceskip=.333em \@plus .15em \@minus .08em \relax
  \xspaceskip=.5em \relax
  \parfillskip=\z@ \@plus 1fil}
\renewenvironment{thebibliography}[1]{%
  \section{References}%
  \list{\@biblabel{\@arabic\c@enumiv}}%
    {\settowidth\labelwidth{\@biblabel{99}}%
     \setlength\leftmargin{18\p@}%
     \setlength\labelsep{2\p@}%
     \setlength\labelwidth{16\p@}%
     \setlength\itemindent{\z@}%
     \setlength\topsep{\z@}%
     \setlength\partopsep{\z@}%
     \setlength\parsep{\z@}%
     \setlength\itemsep{4\p@ \@plus 1\p@ \@minus .5\p@}%
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
\AtBeginDocument{\Urlmuskip=0mu plus 1mu\relax}

%% ---------------------------------------- balance the last page's columns
\ifcs@balance
  \IfFileExists{flushend.sty}{\RequirePackage{flushend}}{%
    \ClassWarning{cs259}{flushend.sty not found; last-page columns will not be balanced}}
\fi

\endinput
