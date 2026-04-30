% theta0max_from_stress
% Stress-limited maximum tip slope angle based on Eq. (8) in
% Hai-Jun Su, "A Pseudorigid-Body 3R Model for Determining
% Large Deflection of Cantilever Beams Subject to Tip Loads."
%
% This script matches the pure-moment case used for Fig. 3.
% For pure moment loading:
%   lambda = 0
%   M_net = eta
%   theta0 = eta
% so Eq. (8) reduces to
%   theta0_max = 2 * (l/t) * (sigma_max/E)

clear;
clc;


% -------- user inputs --------
l_over_t = 100;
sigma_over_E = 0.0104;
% -----------------------------

theta0_max_rad = 2.0 * l_over_t * sigma_over_E;


fprintf('Stress-limited maximum tip slope for pure moment loading\n');
fprintf('l/t           = %.6f\n', l_over_t);
fprintf('sigma_max / E = %.6f\n', sigma_over_E);
fprintf('theta0_max    = %.6f rad\n', theta0_max_rad);

% Example values similar to Fig. 3 in the paper
examples = [
    100, 0.0250;   % polypropylene, about 5 rad
    50,  0.0250;   % polypropylene, about 2.5 rad
    100, 0.0200;   % polyethylene, about 4 rad
    100, 0.0100;   % titanium-like example, about 2 rad
    100, 0.0070;   % aluminum-like example, about 1.4 rad
    500, 0.00087   % steel-like example, about 0.87 rad
];

theta_examples = 2.0 * examples(:, 1) .* examples(:, 2);

fprintf('\nExample table\n');
fprintf('   l/t      sigma/E      theta0_max (rad)   theta0_max (deg)\n');
for i = 1:size(examples, 1)
    fprintf('%8.3f   %8.5f      %12.6f      %12.6f\n', ...
        examples(i, 1), examples(i, 2), ...
        theta_examples(i), rad2deg(theta_examples(i)));
end