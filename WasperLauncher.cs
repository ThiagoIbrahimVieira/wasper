using System;
using System.IO;
using System.Diagnostics;
using System.Windows.Forms;
using System.Threading;

namespace Wasper
{
    static class Program
    {
        [STAThread]
        static void Main(string[] args)
        {
            bool createdNew;
            using (Mutex mutex = new Mutex(true, "WasperSingleInstanceMutex", out createdNew))
            {
                if (!createdNew)
                {
                    MessageBox.Show(
                        "O Wasper já está em execução em segundo plano!\n\nSegure [F8] para ditar em qualquer janela.",
                        "Wasper — Já em Execução",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Information
                    );
                    return;
                }

                string baseDir = AppDomain.CurrentDomain.BaseDirectory;
                string pythonw = Path.Combine(baseDir, ".venv", "Scripts", "pythonw.exe");
                string python = Path.Combine(baseDir, ".venv", "Scripts", "python.exe");
                string script = Path.Combine(baseDir, "main.py");

                string targetPython = File.Exists(pythonw) ? pythonw : python;

                if (!File.Exists(targetPython))
                {
                    MessageBox.Show(
                        "Ambiente virtual do Wasper não encontrado em:\n" + targetPython + "\n\nPor favor, execute 'run_wasper.bat' primeiro.",
                        "Wasper — Erro",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                    return;
                }

                string arguments = "\"" + script + "\"";
                if (args.Length > 0)
                {
                    arguments += " " + string.Join(" ", args);
                }

                ProcessStartInfo psi = new ProcessStartInfo();
                psi.FileName = targetPython;
                psi.Arguments = arguments;
                psi.WorkingDirectory = baseDir;
                psi.UseShellExecute = false;
                psi.CreateNoWindow = true;
                psi.WindowStyle = ProcessWindowStyle.Hidden;

                try
                {
                    Process proc = Process.Start(psi);
                    if (proc != null)
                    {
                        // Aguarda 2.5s para detectar se houve crash prematuro
                        if (proc.WaitForExit(2500))
                        {
                            string crashLog = Path.Combine(baseDir, "wasper_crash.log");
                            string fatalLog = Path.Combine(baseDir, "wasper_fatal.log");
                            string details = "";
                            if (File.Exists(fatalLog)) details = File.ReadAllText(fatalLog);
                            else if (File.Exists(crashLog)) details = File.ReadAllText(crashLog);

                            MessageBox.Show(
                                "O Wasper encerrou inesperadamente durante a inicialização.\n\n" + details,
                                "Wasper — Erro",
                                MessageBoxButtons.OK,
                                MessageBoxIcon.Error
                            );
                            return;
                        }

                        // Mantém a instância única ativa enquanto o Python executa em segundo plano
                        proc.WaitForExit();
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show(
                        "Erro ao iniciar o processo:\n" + ex.Message,
                        "Wasper — Erro",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    );
                }
            }
        }
    }
}
