% PRB_3R_FK_IK


clear;
clc;

gammas = [0.10; 0.35; 0.40; 0.15];
elbowMode = 'down'; % 'down' or 'up'

% Example 1: Forward kinematics
thetaFK = [0.20; 0.15; 0.10];
[QxFK, QyFK, tipSlopeFK] = prb3r_fk(thetaFK, gammas);

fprintf('Forward kinematics example\n');
fprintf('theta = [%.6f %.6f %.6f]\n', thetaFK(1), thetaFK(2), thetaFK(3));
fprintf('Q = [%.6f %.6f]\n', QxFK, QyFK);
fprintf('tip slope = %.6f\n\n', tipSlopeFK);

% Example 2: Inverse kinematics
QxIK = QxFK;
QyIK = QyFK;
tipSlopeIK = tipSlopeFK;

thetaIK = prb3r_ik(QxIK, QyIK, tipSlopeIK, gammas, elbowMode);
[QxCheck, QyCheck, tipSlopeCheck] = prb3r_fk(thetaIK, gammas);

fprintf('Inverse kinematics example\n');
fprintf('target Q = [%.6f %.6f]\n', QxIK, QyIK);
fprintf('target tip slope = %.6f\n', tipSlopeIK);
fprintf('theta = [%.6f %.6f %.6f]\n', thetaIK(1), thetaIK(2), thetaIK(3));
fprintf('reconstructed Q = [%.6f %.6f]\n', QxCheck, QyCheck);
fprintf('reconstructed tip slope = %.6f\n', tipSlopeCheck);
