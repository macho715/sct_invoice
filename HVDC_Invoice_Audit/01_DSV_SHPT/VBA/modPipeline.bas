Attribute VB_Name = "modPipeline"
Option Explicit
'==========================
' Module: modPipeline (���� �籸�� ����)
'==========================

Public Sub START_PIPELINE()
    RunPipeline_Final
End Sub

Public Sub RunPipeline_Final(Optional ByVal ShowMsg As Boolean = True)
    Dim t0 As Single: t0 = Timer
    AppBegin "Final Pipeline"
    On Error GoTo ErrH
    LogActionSafe "PIPELINE", "START"

    ' 1�ܰ�: Formula ����
    SafeRun "ExtractFormulasWithExclusion"
    
    ' 2�ܰ�: REV RATE �� ���
    SafeRun "ApplyFormula_ByDynamicRemark_ExactTotal_Safe"
    
    ' 3�ܰ�: ���� ����
    SafeRun "CompileAllSheets"

Done:
    LogActionSafe "PIPELINE", "END " & Format(Timer - t0, "0.00s")
    AppEnd
    If ShowMsg Then MsgBox "��� ���������� �۾� �Ϸ�!", vbInformation, "Pipeline Complete"
    Exit Sub

ErrH:
    LogActionSafe "PIPELINE", "FATAL ERR: " & Err.description & " (" & Err.Number & ")"
    AppEnd
    If ShowMsg Then MsgBox "���������� �ߴ�: " & vbCrLf & Err.description, vbCritical, "Pipeline Error"
End Sub

Private Sub SafeRun(ByVal ProcName As String)
    On Error GoTo ErrH
    
    If Not ProcExists(ProcName) Then
        Err.Raise 10001, , "���ν��� ����: " & ProcName
    End If

    Application.StatusBar = "Running: " & ProcName & " ..."
    Application.Run ProcName
    LogActionSafe ProcName, "OK"
    Exit Sub

ErrH:
    ' SafeRun���� ���� �߻� ��, ���� ���ν���(RunPipeline_Final)�� ���� ó����� �ѱ�
    Err.Raise Err.Number, "Error in " & ProcName, Err.description
End Sub
